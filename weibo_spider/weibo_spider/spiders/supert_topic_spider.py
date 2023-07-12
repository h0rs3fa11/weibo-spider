import scrapy
import json
from scrapy.utils.project import get_project_settings
from weibo_spider.items import WeiboSpiderItem
from datetime import datetime
import pytz
from lxml import html
from lxml import etree

utc=pytz.UTC

class SuperTopicSpider(scrapy.Spider):
    name = 'super_topic'
    base_url = 'https://m.weibo.cn/api/container/getIndex'
    root_url = 'https://m.weibo.cn'

    settings = get_project_settings()
    filter_group = settings.get('FILTER_GROUP')
    container_id = settings.get('CONTAINER_ID')
    start_date_setting = settings.get('START_DATE')
    end_date_setting = settings.get('END_DATE')
    is_end = False
    full_path = ''
    start_date = utc.localize(datetime.strptime(start_date_setting, "%Y-%m-%d"))
    end_date = utc.localize(datetime.strptime(end_date_setting, "%Y-%m-%d"))
    # debug
    last_id = 4204136049820800
    if filter_group == '最新发帖':
        filter_id = 'sort_time'
    elif filter_group == '最新评论':
        filter_id = 'feed'
    elif filter_group == '热门':
        filter_id = 'recommend'
    else:
        print('Invalid filter group')

    def start_requests(self):
        # url = f'{self.base_url}?containerid={self.container_id}_-_{self.filter_id}&luicode=10000011&lfid={self.container_id}_-_{self.filter_id}'
        url = f'{self.base_url}?jumpfrom=weibocom&containerid={self.container_id}_-_{self.filter_id}&since_id={self.last_id}'

        # first_url = f'https://m.weibo.cn/api/container/getIndex?containerid={self.container_id}_-_{self.filter_id}&luicode=10000011&lfid={self.container_id}_-_{self.filter_id}'

        yield scrapy.Request(url, callback=self.parse, meta={'is_first': True, 'dont_merge_cookies': True, 'dont_filter':True})

    def parse(self, response):
        respData = json.loads(response.text)
        for card in respData['data']['cards']:
            if 'card_group' not in card:
                continue
            # if response.meta.get('is_first'):
            card_group = card['card_group']
            # else:
                # skip the first one
                # card_group = card['card_group'][1:]
            for group in card_group:
                if group['card_type'] != '9':
                    continue
                post_data = group['mblog']
                self.full_path = False
                # 解析格式：Mon Jun 26 07:53:25 +0800 2023
                try:
                    create_time = datetime.strptime(post_data['created_at'], '%a %b %d %X %z %Y')
                except:
                    continue

                if self.start_date > create_time:
                    self.is_end = True
                    break
            
                if self.end_date < create_time:
                    continue

                # parse item
                post = WeiboSpiderItem()
                post['id'] = post_data['id']
                try:
                    post['user_id'] = post_data['user']['id']
                    post['screen_name'] = post_data['user']['screen_name']
                    post['profile_url'] = post_data['user']['profile_url']
                except:
                    post['user_id'] = '-1'
                    post['screen_name'] = '已封禁账号'
                    post['profile_url'] = ''

                post['text'] = self.parse_html_content(post_data['text'])
                
                if 'region_name' in post_data:
                    post['location'] = post_data['region_name'][4:]
                else:
                    post['location'] = '无'
                post['create_at'] = post_data['created_at']
                
                if self.full_path:
                    yield scrapy.Request(f'{self.root_url}/statuses/extend?id={post["id"]}', callback=self.parse_full_content, meta={'data': post})
                else:
                    yield post

        # 更新last_id
        try:
            self.last_id = respData['data']['pageInfo']['since_id']
        except:
            # 如果respData['msg']=='这里还没有内容' 重试一次
            if respData['msg'] == '这里还没有内容':
                url = f'{self.base_url}?jumpfrom=weibocom&containerid={self.container_id}_-_{self.filter_id}&since_id={self.last_id}'
                yield scrapy.Request(url=url, callback=self.parse, meta={'is_first': False, 'dont_merge_cookies': True, 'dont_filter':True})

        if not self.is_end:
            url = f'{self.base_url}?jumpfrom=weibocom&containerid={self.container_id}_-_{self.filter_id}&since_id={self.last_id}'
            yield scrapy.Request(url=url, callback=self.parse, meta={'is_first': False, 'dont_merge_cookies': True, 'dont_filter':True})

    def parse_full_content(self, response):
        post = response.meta.get('data')
        post['text'] = ''
        try:
            content = json.loads(response.text)
            html_text = content['data']['longTextContent']
            post['text'] = self.parse_html_content(html_text)
        except:
            post['text'] = '通过接口无法查看内容（请前往微博客户端查看）'
        yield post
        

    def parse_html_content(self, html_content):
        html_document = html.fromstring(html_content)
        word_list = html_document.xpath('//text()')

        def remove_empty_strings(string):
            return string != "" and string != " "
        
        filtered_list = list(filter(remove_empty_strings, word_list))
        try:
            if filtered_list[0] == '精神分裂症':
                filtered_list = filtered_list[1:]
            if len(filtered_list) == 0:
                content = '无文字内容'
                return content
            if filtered_list[-1] == '全文':
                self.full_path = True
                filtered_list.pop()

            content = ' '.join(filtered_list)
        except:
            content = '无文字内容'
        return content