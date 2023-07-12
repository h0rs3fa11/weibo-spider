# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WeiboSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    user_id = scrapy.Field()
    screen_name = scrapy.Field()
    profile_url = scrapy.Field()
    text = scrapy.Field()
    location = scrapy.Field()
    create_at = scrapy.Field()
