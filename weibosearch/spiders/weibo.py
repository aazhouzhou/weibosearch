# -*- coding: utf-8 -*-
from scrapy import Spider, FormRequest, Request
import re

from weibosearch.items import WeiboItem


class WeiboSpider(Spider):
    name = "weibo"
    allowed_domains = ["weibo.cn"]
    search_url = 'https://weibo.cn/search/mblog'
    max_page = 100#通过测试最多可以200

    def start_requests(self):
        keyword = '000001'
        url = '{url}?keyword={keyword}'.format(url=self.search_url, keyword=keyword)
        for page in range(self.max_page + 1):
            data = {
                'mp': str(self.max_page),
                'page': str(page)
            }
            yield FormRequest(url, callback=self.parse_index, formdata=data)

    #获取微博详情页链接

    #先得到想要解析的部分，然后再进行更细的抽取，如果直接利用response.path判断是否是转发的微博就会出错！
    def parse_index(self, response):
        weibos = response.xpath('//div[@class="c" and contains(@id, "M_")]')
        #print(weibos)
        for weibo in weibos:
            is_forward = bool(weibo.xpath('.//span[@class="cmt"]').extract_first())#判断是否是转发的微博
            #print(is_forward)
            if is_forward:
                detail_url = weibo.xpath('.//a[contains(., "原文评论[")]//@href').extract_first()#抽取原文评论链接
            else:
                detail_url = weibo.xpath('.//a[contains(., "评论[")]//@href').extract_first()  # 抽取转发评论链接
            #print(detail_url)
            yield Request(detail_url, callback=self.parse_detail)


    #解析微博详情
    # 通过对index页面解析出的索引url进行re正则匹配的到id
    def parse_detail(self, response):
        id = re.search('comment\/(.*?)\?', response.url).group(1)
        url = response.url
        content = ''.join(response.xpath('//div[@id="M_"]//span[@class="ctt"]/text()')[0].extract().replace('\u200b', ''))#最后返回的内容是列表形式，通过join将里面的每一条进行拼接，得到一条完整的内容，replace('\u200b', '')是把末尾不能解析的字符去掉
        print(id, url, content)
        #评论
        comment_count = response.xpath('//span[@class="pms"]/text()').re_first('评论\[(.*?)\]')
        #转发
        forward_count = response.xpath('//a[contains(.,"转发[")]/text()').re_first('转发\[(.*?)\]')
        #赞
        like_count = response.xpath('//a[contains(.,"赞[")]').re_first('赞\[(.*?)\]')
        print(comment_count, forward_count, like_count)
        #时间
        posted_at = response.xpath('//div[@id="M_"]//span[@class="ct"]//text()').extract_first(default=None)
        #发布人
        user = response.xpath('//div[@id="M_"]/div[1]/a/text()').extract_first(default=None)
        print(posted_at, user)

        weibo_item = WeiboItem()
        #eval()可以动态获取变量名，动态进行赋值,由于eval使用起来比较危险，对于不存在的变量这里由field代替，就会产生错误中断程序，因此要try except一下，抛出异常
        for field in weibo_item.fields:
            try:
                weibo_item[field] = eval(field)
            except NameError:
                self.logger.debug('Field is Not Defined' + field)
        yield weibo_item