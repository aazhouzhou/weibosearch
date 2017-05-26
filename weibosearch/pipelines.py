# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

#数据清洗
import pymongo

from weibosearch.items import WeiboItem
import time
import re

class WeiboPipeline(object):

    #页面显示的时间格式主要有几分钟前，几月几日几时，今天几点几点，总结规律，如果是在离当前时间一小时以内发送的就会显示多少分钟前，如果超过一小时属于当天就会是今天几点几点
    def parse_time(self, datetime):
        #\d匹配数字
        #strftime()是一种计算机函数,strftime() 函数根据区域设置格式化本地时间/日期,函数的功能将时间格式化,
        if re.match('\d+月\d+日', datetime):
            datetime = time.strftime('%Y年', time.localtime()) + datetime
        if re.match('\d+分钟前', datetime):
            minute = re.match('(\d+)', datetime).group(1)#\d+是0到9的数字至少出现一次，在正则表达式中，group用来打印（）中匹配的内容，打印匹配第几个括号里的内容，就使用group(几)
            # time.localtime()是获取时间戳，如果不传入参数，默认当前时间,通过time.time()获得当前时间戳再减去刚刚获得的秒数乘以60
            datetime = (time.strftime('%Y{y}%m{m}%d{d} %H:%M', time.localtime(time.time() - float(minute) * 60))).format(y='年', m='月', d='日')
        if re.match('今天.*', datetime):
            datetime = re.match('今天(.*)', datetime).group(1).strip()
            datetime = (time.strftime('%Y{y}%m{m}%d{d}', time.localtime()) + ' ' + datetime).format(y='年', m='月', d='日')
            #datetime = re.match('今天(.*)', datetime).group(1).strip()
            #datetime = time.strftime('%Y年%m月%d日', time.localtime()) + ' ' + datetime

        return datetime

    def process_item(self, item, spider):
        if isinstance(item, WeiboItem):
            # 处理content部分，如是就进行改写，将其内容开始部分的冒号去掉，同时去掉左右两边的空格
            if item.get('content'):
                item['content'] = item['content'].lstrip(':').strip()
            #处理时间，先把空格去掉，再通过parse_time进行详细处理
            if item.get('posted_at'):
                item['posted_at'] = item['posted_at'].strip()
                item['posted_at'] = self.parse_time(item['posted_at'])
            return item



class MongoPipeline():
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri #数据库连接url，指定哪个端口等
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

#在pipeline里面复写了open_spider方法，等爬虫开启时自动执行这个复写的open_spider
    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri) #开启mongodb的数据库连接
        self.db = self.client[self.mongo_db] #创建连接数据库的连接信息

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        #item去重：
        # 利用table_name属性，调用一下传过来，通过update进行更新，通过id查询，将传入的item转成字典形式，true表示查询到内容就对他进行更新，没有查询到就对他进行插入
        self.db[item.table_name].update({'id': item.get('id')}, {'$set': dict(item)}, True)
        return item



