# Copyright 2019, Hyeongdo Lee. All Rights Reserved.
# 
# e-mail: mylovercorea@gmail.com
#
# ==============================================================================
"""Implementation of Instagram Photo Crawler (Simple Ver.)
"""
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options

# Constants
HOST = 'http://www.instagram.com'


class InstagramCrawler:
    """Crawler main class"""

    def __init__(self, firefox_path=None):
        binary = FirefoxBinary(firefox_path)
        # Headless browser
        options = Options()
        options.headless = True
        self._driver = webdriver.Firefox(firefox_binary=binary, options=options)

    def crawl(self):
        print('Headless Firefox Initialized')
        self._driver.quit()

    def browse_target_page(self, query):
        pass


def main():
    crawler = InstagramCrawler()
    crawler.crawl()


if __name__ == '__main__':
    main()
