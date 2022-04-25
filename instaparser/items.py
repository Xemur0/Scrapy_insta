# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    _id = scrapy.Field()
    source_id = scrapy.Field()
    source_name = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    user_fullname = scrapy.Field()
    photo_url = scrapy.Field()
    subs_type = scrapy.Field()
