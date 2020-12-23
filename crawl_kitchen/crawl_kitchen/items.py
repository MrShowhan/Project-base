# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlKitchenItem(scrapy.Item):
    base_food = scrapy.Field()
    cook = scrapy.Field()
    name = scrapy.Field()
    introduce = scrapy.Field()
    score = scrapy.Field()
    cooked = scrapy.Field()
    _id = scrapy.Field()