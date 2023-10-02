from selenium_crawler import OroroSeleniumCrawler
from subs_downloader import OroroSubtitlesScraper


if __name__ == "__main__":
    crawler = OroroSeleniumCrawler(
        data_to_crawl=...
    )
    crawler.crawl()
    scraper = OroroSubtitlesScraper(
        data_to_scrape=crawler.data_to_crawl,
        language=...,
        cookies=crawler.cookies
    )
    scraper.scrape()
