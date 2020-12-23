# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from crawl_kitchen.items import CrawlKitchenItem


class KitchenSpider(CrawlSpider):
    name = 'kitchen'
    allowed_domains = ['xiachufang.com']
    start_urls = ['http://www.xiachufang.com/category/']

    rules = (
        Rule(LinkExtractor(allow=r'/category/\d+/'), follow=True),
        Rule(LinkExtractor(allow=r'/category/\d+/?page=\d+'), follow=True),
        Rule(LinkExtractor(allow=r'/recipe/\d+/'), callback='parse_item'),
    )

    def parse_item(self, response):
        item = CrawlKitchenItem()
        item['base_food'] = self.get_base_food(response)
        item["cook"] = self.get_cook(response)
        item['name'] = self.get_name(response)
        item['introduce'] = self.get_introduce(response)
        item['score'] = self.get_score(response)
        item['cooked'] = self.get_cooked(response)
        yield item

    def get_name(self, response):
        name = response.xpath('//h1[@class="page-title"]/text()').extract_first()
        name = name.strip()
        return name

    def get_introduce(self, response):
        introduce = response.xpath('//div[@class="desc mt30"]/text()').extract_first()
        if introduce:
            introduce = introduce.strip()
        else:
            introduce = '暂无简介'
        return introduce

    def get_score(self, response):
        score = response.xpath('//div[@class="score float-left"]/span/text()').extract()
        if score:
            score = score[1] + score[0]
        else:
            score = '暂无评分'
        return score

    def get_cooked(self, response):
        cooked = response.xpath('//div[@class="cooked float-left"]/span/text()').extract()
        cooked = cooked[0] + cooked[1]
        return cooked

    def get_base_food(self, response):
        result = response.xpath('//div[@class="ings"]//tr//text()').extract()
        result = [i.strip() for i in result]
        result = [i for i in result if len(i) > 0]
        result = dict(zip(result[0::2], result[1::2]))
        return result

    def get_cook(self, response):
        result = response.xpath('//div[@class="steps"]//li/p/text()').extract()
        j = 1
        for i in range(len(result)):
            result[i] = "第{}步:".format(j) + result[i]
            j += 1
        return result