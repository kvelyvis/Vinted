import scrapy
import logging
from scrapy.loader import ItemLoader
from ..items import VintedItem
from datetime import datetime
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class VintedSpider(scrapy.Spider):
    name = "vintedspider"
    scrape_time: str

    def __init__(self, **kwargs):
        self.scrape_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.safe_scrape_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        super().__init__(**kwargs)

        options = FirefoxOptions()
        # options.add_argument("--headless")  # activate if headless browser mode wanted
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 20)

    def start_requests(self):
        # urls_list = ["https://www.vinted.lt/vyrams/batai/sportine-avalyne",
        #              "https://www.vinted.lt/moterims/batai/kedai-1916"
        #              ]
        #
        # for url in urls_list:
        #     yield scrapy.Request(url, self.parse_category)

        # yield scrapy.Request(
        #     "https://www.vinted.lt/vyrams/batai/sportine-avalyne",
        #     self.parse_category,
        # )
        yield scrapy.Request(
           "https://www.vinted.lt/vyrams/batai/sportine-avalyne/turistiniai-batai/2617751727-puma-korki",
           self.parse_clothing,
        )

    def parse_category(self, response):
        self.driver.get(response.url)
        time.sleep(2)

        if self.driver.find_elements(By.XPATH, "//div[@class='ot-sdk-container']"):
            cookies_button = self.driver.find_element(
                By.XPATH,
                "//div[@class='ot-sdk-container']//button[@id='onetrust-accept-btn-handler']",
            )
            cookies_button.click()

        clothing_list_messy = self.driver.find_elements(
            By.XPATH,
            "//div[@class='feed-grid']/div/div/div/div/div[@class='web_ui__ItemBox__image-container']"
            "/a[@class='web_ui__ItemBox__overlay'] ",
        )

        clothing_url_list = []
        for clothing in clothing_list_messy:
            clothing_href = clothing.get_attribute("href")
            clothing_url_list.append(clothing_href)

        for clothing_url in clothing_url_list:
            yield response.follow(clothing_url, self.parse_clothing)

        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.web_ui__Card__card div.web_ui__Pagination__pagination.web_ui__Pagination__parent "
            "a[class='web_ui__Pagination__next']",
        ):
            next_page = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.web_ui__Card__card div.web_ui__Pagination__pagination.web_ui__Pagination__parent "
                "a[class='web_ui__Pagination__next']",
            )
            if next_page is not None:
                next_page.click()
                next_url = self.driver.current_url
                yield response.follow(next_url, self.parse_category)

    def parse_clothing(self, response):
        loader = ItemLoader(item=VintedItem(), response=response)

        logger.info(f"scraping = {response.url}")

        self.driver.get(response.url)
        time.sleep(1)

        loader.add_value("url", response.url)
        loader.add_value("scrape_time", self.scrape_time)

        # title
        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.web_ui__Cell__body div "
            "h2.web_ui__Text__text.web_ui__Text__title.web_ui__Text__left ",
        ):
            title = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.web_ui__Cell__body div "
                "h2.web_ui__Text__text.web_ui__Text__title.web_ui__Text__left ",
            ).get_attribute("textContent")
            if not 3 < len(title) < 200:
                logger.error(
                    f"expected title length between 3 and 200, got length = {len(title)}"
                )
                logger.error(f"url = {response.url}")
                return
        else:
            title = False
        loader.add_value("title", title)

        # price
        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.details-list.details-list--pricing div.details-list__item.details-list--price "
            "div div.u-flexbox.u-justify-content-between "
            "h1.web_ui__Text__text.web_ui__Text__heading.web_ui__Text__left ",
        ):
            price = (
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div.details-list.details-list--pricing div.details-list__item.details-list--price "
                    "div div.u-flexbox.u-justify-content-between "
                    "h1.web_ui__Text__text.web_ui__Text__heading.web_ui__Text__left ",
                )
                .get_attribute("textContent")
                .replace("\xa0", " ")
            )
            if not 3 < len(price) < 13:
                logger.error(
                    f"expected price length between 3 and 13, got length = {len(price)}"
                )
                logger.error(f"url = {response.url}")
                return
        else:
            price = False
        loader.add_value("price", price)

        # seller
        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.web_ui__Cell__content div.web_ui__Cell__heading div.web_ui__Cell__title div.u-flexbox.u-align-items-center span.web_ui__Text__text",
        ):
            seller = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.web_ui__Cell__content div.web_ui__Cell__heading div.web_ui__Cell__title div.u-flexbox.u-align-items-center span.web_ui__Text__text",
            ).get_attribute("textContent")
            if not 1 <= len(seller) < 50:
                logger.error(
                    f"expected seller length between 1 and 50, got length = {len(seller)}"
                )
                logger.error(f"url = {response.url}")
                return
        else:
            seller = False
        loader.add_value("seller", seller)

        # seller items count
        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.c-label--default.c-label div.c-label__content h3.c-text--subtitle.c-text--left.c-text",
        ):
            seller_items = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.c-label--default.c-label div.c-label__content h3.c-text--subtitle.c-text--left.c-text",
            ).get_attribute("textContent")
            if not 1 <= len(seller_items) < 30:
                logger.error(
                    f"expected seller items length between 1 and 30, got length = {len(seller_items)}"
                )
                logger.error(f"url = {response.url}")
                return
            elif "Nario prek" not in seller_items:
                logger.info(f"substring Nario prekes not in seller_items string")
                logger.info(f"url = {response.url}")

            seller_items_count_list = re.findall(r"\b\d+\b", seller_items)
            if len(seller_items_count_list) == 0:
                if "Panašios prekės" in seller_items:
                    seller_items_count = '1'
                else:
                    logger.error(
                        f"if seller items count list length = 0, then string Panasios prekes should be inside seller_items (= {seller_items})"
                    )
                    logger.error(f"url = {response.url}")
                    return
            elif len(seller_items_count_list) == 2:
                seller_items_count = "".join(seller_items_count_list)
            elif len(seller_items_count_list) == 1:
                seller_items_count = seller_items_count_list[0]
            else:
                logger.error(
                    f"expected seller items count list length = 0, 1 or 2, got length = {len(seller_items_count_list)}"
                )
                logger.error(f"url = {response.url}")
                return

            if not seller_items_count.isdigit():
                logger.error(f"seller items count is not digit")
                logger.error(f"url = {response.url}")
                return
        else:
            seller_items_count = False
        loader.add_value("seller_items_count", seller_items_count)

        # description handwritten
        if self.driver.find_elements(
            By.CSS_SELECTOR, "div.web_ui__Cell__body div.u-text-wrap span"
        ):
            description = (
                self.driver.find_element(
                    By.CSS_SELECTOR, "div.web_ui__Cell__body div.u-text-wrap span"
                )
                .get_attribute("textContent")
                .replace("\n", "")
            )
            if not 3 < len(description) < 5000:
                logger.error(
                    f"expected description length between 3 and 5000, got length = {len(description)}"
                )
                logger.error(f"url = {response.url}")
                return
        else:
            description = False
        loader.add_value("description", description)

        # casual description (brand, size, color etc)
        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.details-list.details-list--main-info div.details-list.details-list--details",
        ):
            description_names_messy_list = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.details-list.details-list--main-info div.details-list.details-list--details "
                "div.details-list__item div.details-list__item-title ",
            )
            if not 1 <= len(description_names_messy_list) < 10:
                logger.error(
                    f"expected description names length between 1 and 10, got length = {len(description_names_messy_list)}"
                )
                logger.error(f"url = {response.url}")
                return

            description_info_messy_list = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.details-list.details-list--main-info div.details-list.details-list--details "
                "div.details-list__item div.details-list__item-value ",
            )
            if not 1 <= len(description_info_messy_list) < 10:
                logger.error(
                    f"expected description names length between 1 and 10, got length = {len(description_info_messy_list)}"
                )
                logger.error(f"url = {response.url}")
                return
            elif len(description_info_messy_list) != len(description_names_messy_list):
                logger.error(
                    f"description names and description info length is not the same, check it"
                )
                logger.error(f"url = {response.url}")
                return
        else:
            description_names_messy_list = []
            description_info_messy_list = []

        description_names_list = []
        if description_names_messy_list:
            for description_name in description_names_messy_list:
                description_name_new = description_name.get_attribute("textContent")
                description_names_list.append(description_name_new)

        description_info_list = []
        if description_info_messy_list:
            for description_info in description_info_messy_list:
                description_info_new = description_info.get_attribute("textContent")
                description_info_list.append(description_info_new)

        description_clean_name_list = []
        for item in description_names_list:
            if "\n" in item:
                item = item.replace("\n", "").strip()

            description_clean_name_list.append(item)

        description_clean_info_list = []
        for item in description_info_list:
            if "\xa0" in item:
                item = item.replace("\xa0", "")

            if "Mėgti" in item:
                item = item.replace("Mėgti", "")

            if "Condition information" in item:
                item = item.split("Condition")[0]

            if "Size information" in item:
                item = item.split("Size")[0]

            if "\n" in item:
                item = item.replace("\n", "").strip()

            description_clean_info_list.append(item)

        description_combined_dict = dict(
            zip(description_clean_name_list, description_clean_info_list)
        )
        for key in description_combined_dict.keys():
            if "ženklas" in key:
                brand = description_combined_dict[key]
                if not 1 <= len(brand) < 100:
                    logger.error(
                        f"expected brand length between 1 and 100, got length = {len(brand)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("brand", brand)

            if "Būklė" in key:
                condition = description_combined_dict.get(key)
                if not 3 < len(condition) < 20:
                    logger.error(
                        f"expected condition length between 3 and 20, got length = {len(condition)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("condition", condition)

            if "Vietovė" in key:
                location = description_combined_dict.get(key)
                if not 3 < len(location) < 50:
                    logger.error(
                        f"expected location length between 3 and 50, got length = {len(location)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("location", location)

            if "Mokėjimo būdai" in key:
                payment = description_combined_dict.get(key)
                if not 3 < len(payment) < 40:
                    logger.error(
                        f"expected payment length between 3 and 40, got length = {len(payment)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("payment", payment)

            if "Peržiūrėta" in key:
                views = description_combined_dict.get(key)
                if not 1 <= len(views) < 10:
                    logger.error(
                        f"expected views length between 1 and 10, got length = {len(views)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("views", views)

            if "Domisi" in key:
                interested = description_combined_dict[key]
                if not 1 <= len(interested) < 10:
                    logger.error(
                        f"expected interested length between 1 and 10, got length = {len(interested)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("interested", interested)

            if "Įkelta" in key:
                uploaded = description_combined_dict[key]
                if not 1 <= len(uploaded) < 20:
                    logger.error(
                        f"expected uploaded length between 1 and 20, got length = {len(uploaded)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("uploaded", uploaded)

            if "Dydis" in key:
                size = description_combined_dict.get(key)
                if not 1 <= len(size) < 20:
                    logger.error(
                        f"expected size length between 1 and 20, got length = {len(size)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("size", size)

            if "Spalva" in key:
                colour = description_combined_dict.get(key)
                if not 1 <= len(colour) < 40:
                    logger.error(
                        f"expected colour length between 1 and 40, got length = {len(colour)}"
                    )
                    logger.error(f"url = {response.url}")
                    return

                loader.add_value("colour", colour)

        category_messy_list = self.driver.find_elements(
            By.CSS_SELECTOR,
            "nav.catalog-nav ul.breadcrumbs.breadcrumbs--compact"
            ".breadcrumbs--truncated "
            "li.breadcrumbs__item a span",
        )

        if category_messy_list:
            category_list = [
                cat.get_attribute("textContent") for cat in category_messy_list
            ][1:]
            category = " | ".join(category_list)
            if not 1 <= len(category) < 200:
                logger.error(
                    f"expected category length between 1 and 200, got length = {len(category)}"
                )
                logger.error(f"url = {response.url}")
                return

            loader.add_value("category", category)

        #availability status
        if self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.c-cell--success.c-cell div.c-cell__content div.c-cell__body",
        ):
            status = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.c-cell--success.c-cell div.c-cell__content div.c-cell__body",
            ).get_attribute("textContent").split()
        else:
            status = "Available"

        loader.add_value("status", status)

        return loader.load_item()

    # def close(self, reason):
    #     self.driver.quit()
