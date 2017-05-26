# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json

import requests

from requests.exceptions import ConnectionError
import logging
#exception异常
#中间件文件定义cookie相关信息，改写爬虫那边的request请求,还有一些关于封号的问题
from scrapy.exceptions import IgnoreRequest


class CookiesMiddleware():

    #定义一个日志输出的类，代替print输出
    def __init__(self, cookies_pool_url):
        self.logger = logging.getLogger(__name__)
        self.cookies_pool_url = cookies_pool_url

    #用到之前的cookie池，请求接口，即cookies_pool_url拿到cookie值,网页内容用json解析一下
    def _get_random_cookies(self):
        try:
            response = requests.get(self.cookies_pool_url)
            if response.status_code == 200:
                return json.loads(response.text)
        except ConnectionError:
            return None
    #将url配置成可变参数，通过定义这个方法将url配置到全局的setting里面，从setting里面获得全局的配置信息
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            cookies_pool_url=crawler.settings.get('COOKIES_POOL_URL')
        )

    #通过_get_random_cookies()函数拿到cookie，判断cookies是否正常获取，最后对request进行改写
    #如果获取到cookies的话，就对request.cookies进行改写，json.dumps是将对象以字符串形式展现
    def process_request(self, request, spider):
        cookies = self._get_random_cookies()
        if cookies:
            request.cookies = cookies
            self.logger.debug('Using Cookies' + json.dumps(cookies))
        else:
            self.logger.debug('No Valid Cookies')

    #针对微博的反爬虫措施，可能会跳转到封号的一些页面去
    def process_response(self, request, response, spider):
        if response.status in [300, 301, 302, 303]:
            try:
                redirect_url = response.headers['location']#通过拿到redirect_url这个重定向的url
                if 'passport' in redirect_url:
                    self.logger.warning('Need Login, Updating Cookies')#重定向url包含passport，说明cookie失效
                elif 'weibo.cn/security' in redirect_url:
                    self.logger.warning('Account  is Locked!')#重定向url包含weibo.cn/security，说明账号被封
                request.cookies = self._get_random_cookies()#重新对其进行cookie的替换，再重新进行调度
                return request  #return以后就会重新加入到队列里面去
            except:
                raise IgnoreRequest
        #414超时导致，重新对request进行调度即可
        elif response.status in [414]:
            return request
        else:
            return response