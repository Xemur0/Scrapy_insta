import scrapy
import json
import re
from scrapy.http import HtmlResponse
from instaparser.items import InstaparserItem
from urllib.parse import urlencode
from copy import deepcopy
from variablesinst import USER_PWD, USER_NAME


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    instagram_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    insta_login = USER_NAME
    insta_pwd = USER_PWD
    parse_users = ['elli.piano', 'kaada.music']
    insta_api_link = 'https://i.instagram.com/api/v1/'

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.instagram_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.insta_login,
                      'enc_password': self.insta_pwd},
            headers={'X-CSRFToken': csrf}
        )


    def login(self, response: HtmlResponse):
        j_body = response.json()
        if j_body.get('authenticated'):
            for user in self.parse_users:
                yield response.follow(
                    f'/{user}/',
                    callback=self.user_data_parse,
                    cb_kwargs={'username': user}
                )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)

        variables = {
            'count': 12
        }

        followers_url = f'{self.insta_api_link}friendships/{user_id}/' \
                        f'followers/?{urlencode(variables)}' \
                        f'&search_surface=follow_list_page'

        subscriptions_url = f'{self.insta_api_link}friendships/' \
                            f'{user_id}/following/?{urlencode(variables)}'


        yield response.follow(followers_url,
                              callback=self.user_followers_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)
                                         },
                              headers={'User-Agent':
                                           'Instagram 155.0.0.37.107'}
                              )
        yield response.follow(subscriptions_url,
                              callback=self.user_subscriptions_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)
                                         },
                              headers={'User-Agent':
                                           'Instagram 155.0.0.37.107'}
                              )

    def user_subscriptions_parse(self, response: HtmlResponse,
                                 username, user_id, variables):
        j_data = response.json()
        has_more_subscriptions = j_data.get('big_list')

        if has_more_subscriptions:
            variables['max_id'] = j_data.get('next_max_id')
            subscriptions_url = f'{self.insta_api_link}friendships' \
                                f'/{user_id}/following/?{urlencode(variables)}'
            yield response.follow(subscriptions_url,
                                  callback=self.user_subscriptions_parse,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'variables': deepcopy(variables),
                                             },
                                  headers={'User-Agent':
                                               'Instagram 155.0.0.37.107'}
                                  )
        subscriptions = j_data.get('users')
        for subscription in subscriptions:
            item = InstaparserItem(
                source_id=user_id,
                source_name=username,
                user_id=subscription['pk'],
                user_name=subscription['username'],
                user_fullname=subscription['full_name'],
                photo_url=subscription['profile_pic_url'],
                subs_type='subscription'
            )

            yield item

    def user_followers_parse(self, response: HtmlResponse, username, user_id, variables):
        j_data = response.json()
        has_more_subscribers = j_data.get('big_list')

        if has_more_subscribers:
            variables['max_id'] = j_data.get('next_max_id')
            followers_url = f'{self.insta_api_link}friendships/' \
                            f'{user_id}/followers/?{urlencode(variables)}' \
                            f'&search_surface=follow_list_page'
            yield response.follow(followers_url,
                                  callback=self.user_followers_parse,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'variables': deepcopy(variables),
                                             },
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'}
                                  )

        followers = j_data.get('users')
        for follower in followers:
            item = InstaparserItem(
                source_id=user_id,
                source_name=username,
                user_id=follower['pk'],
                user_name=follower['username'],
                user_fullname=follower['full_name'],
                photo_url=follower['profile_pic_url'],
                subs_type='subscriber'
            )
            yield item

    def fetch_csrf_token(self, text):
        """ Get csrf-token for auth """
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        try:
            matched = re.search(
                '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
            ).group()
            return json.loads(matched).get('id')
        except:
            return re.findall('\"id\":\"\\d+\"', text)[-1].split('"')[-2]