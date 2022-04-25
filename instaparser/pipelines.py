# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import scrapy
import os
from pymongo import MongoClient
from itemadapter import ItemAdapter


class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('127.0.0.1', 27017)
        db_name = 'instagram'
        self.mongo_base = client.get_database(db_name)

    def process_item(self, item, spider):
        collection = self.mongo_base[item.get('source_name')]
        collection.insert_one(item)
        return item