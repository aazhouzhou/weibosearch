# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class WeiboItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    table_name = 'weibo'#用于后面对数据库进行插入操作

    id = Field()
    url = Field()
    content = Field()
    forward_count = Field()
    comment_count = Field()
    like_count = Field()
    posted_at = Field()
    user = Field()

