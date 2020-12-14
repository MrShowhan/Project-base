# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

class CrawlKitchenPipeline(object):
    def __init__(self):
        # 配置数据库信息
        self.MONGO_URl = 'localhost'
        self.MONGO_DB = 'test'  # 数据库名
        self.MONGO_TABLE = 'cookies'  # 表名

    def process_item(self, item, spider):
        self.save_url_to_Mongo(item)

    def save_url_to_Mongo(self, result):
        client = pymongo.MongoClient(self.MONGO_URl)
        db = client[self.MONGO_DB]
        try:
            if db[self.MONGO_TABLE].insert(result):
                print('存储到MongoDB成功', result)
        except Exception:
            print('存储到MongoDb失败', result)
