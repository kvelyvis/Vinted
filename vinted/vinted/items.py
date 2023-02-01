import scrapy


class VintedItem(scrapy.Item):
    url = scrapy.Field()
    scrape_time = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    seller = scrapy.Field()
    seller_items_count = scrapy.Field()
    description = scrapy.Field()
    brand = scrapy.Field()
    size = scrapy.Field()
    colour = scrapy.Field()
    condition = scrapy.Field()
    location = scrapy.Field()
    category = scrapy.Field()
    payment = scrapy.Field()
    views = scrapy.Field()
    interested = scrapy.Field()
    uploaded = scrapy.Field()
    status = scrapy.Field()

