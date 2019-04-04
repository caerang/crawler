# Copyright 2019, Hyeongdo Lee. All Rights Reserved.
# 
# e-mail: mylovercorea@gmail.com
#
# ==============================================================================
"""
"""
import argparse
import codecs
from collections import defaultdict
import json
import os
import re
import sys
import time
from urllib.parse import urljoin
from urllib.request import urlretrieve
import requests
import selenium
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# HOST
HOST = 'http://www.instagram.com'


# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = 'a._1cr2e._epyes'
CSS_RIGHT_ARROW = "a[class='_de018 coreSpriteRightPaginationArrow']"
FIREFOX_FIRST_POST_PATH = "//div[contains(@class, '_8mlbc _vbtk2 _t5r8b')]"
TIME_TO_CAPTION_PATH = '../../../div/ul/li/span'

# FOLLOWERS/FOLLOWING RELATED
CSS_EXPLORE = "a[href='/explore/']"
CSS_LOGIN = "a[href='/accounts/login/']"
CSS_FOLLOWERS = "a[href='/{}/followers/']"
CSS_FOLLOWING = "a[href='/{}/following/']"
FOLLOWER_PATH = "//div[contains(text(), 'Followers')]"
FOLLOWING_PATH = "//div[contains(text(), 'Following')]"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"


class UrlChange:

    def __init__(self, prev_url):
        self._prev_url = prev_url

    def __call__(self, driver):
        return self._prev_url != driver.current_url


class InstagramCrawler:

    def __init__(self, headless=True, firefox_path=None):
        if headless:
            print('headless mode on')
            self._driver = webdriver.PhantomJS()
        else:
            binary = FirefoxBinary(firefox_path)
            options = Options()
            options.headless = True
            self._driver = webdriver.Firefox(firefox_binary=binary, options=options)

        self._driver.implicitly_wait(10)
        self._data = defaultdict(list)

    def login(self, authentication=None):
        self._driver.get(urljoin(HOST, 'accounts/login/'))

        if authentication:
            print(f'Username and password loaded from {authentication}')
            with open(authentication, 'r') as fin:
                auth_dict = json.loads(fin.read())

            username_input = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.NAME, 'username'))
            )
            username_input.send_keys(auth_dict['username'])

            password_input = WebDriverWait(self._driver, 5).until(
                EC.presence_of_element_located((By.NAME, 'password'))
            )
            password_input.send_keys(auth_dict['password'])

            password_input.submit()
        else:
            print('Type your username and password by hand to login!')
            print('You have a minute to do so!')

        print('')
        WebDriverWait(self._driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, CSS_EXPLORE))
        )

    def quit(self):
        self._driver.quit()

    def crawl(self, dir_prefix, query, crawl_type, number, caption, authentication):
        print(f'dir_prefix: {dir_prefix}, query: {query}, crawl_type: {crawl_type}, number: {number},'
        f'caption: {caption}, authentication: {authentication}')

        if crawl_type == 'photos':
            self.browse_target_page(query)
            self.scroll_to_num_of_posts(number)
            self.scrape_photo_links(number, is_hastag=query.startswith('#'))
            if caption is True:
                self.click_and_scrape_captions(number)

        elif crawl_type in ['followers', 'following']:
            print(f'You will need to login to crawl {crawl_type}')
            self.login(authentication)

            assert not query.startswith('#'), 'Hashtag does not have followers/following!'
            self.browse_target_page(query)
            self.scrape_followers_or_following(crawl_type, query, number)
        else:
            print('Unknown crawl type: {crawl_type}')
            self.quit()
            return

        print('Saving...')
        self.download_and_save(dir_prefix, query, crawl_type)

        print('Quitting driver...')
        self.quit()

    def browse_target_page(self, query):
        if query.startswith('#'):
            relative_url = urljoin('explore/tags/', query.strip('#'))
        else:
            relative_url = query

        target_url = urljoin(HOST, relative_url)

        self._driver.get(target_url)

    def scroll_to_num_of_posts(self, number):
        num_info = re.search(r'\{"count":\d+', self._driver.page_source).group()
        num_of_posts = int(re.findall(r'\d+', num_info)[0])
        print(f'posts: {num_of_posts}, number: {number}')
        number = number if number < num_of_posts else num_of_posts
        try:
            load_more = WebDriverWait(self._driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, CSS_LOAD_MORE))
            )
        except TimeoutException:
            self.quit()
        finally:
            load_more.click()

        num_to_scroll = int((number - 12) / 12) + 1
        for _ in range(num_to_scroll):
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(0.2)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(0.2)

    def scrape_photo_links(self, number, is_hashtag=False):
        print('Scraping photo links...')
        encased_photo_links = re.finditer(r'src="([https]+:...[\/\w \.=]*..[\/\w \.=]*'
                                          r'..[\/\w \.-]*..[\/\w \.-].jpg)', self._driver.page_source)

        photo_links = [m.group(1) for m in encased_photo_links]
        print(f'Number of photo_links: {len(photo_links)}')
        begin = 0 if is_hashtag else 1
        self._data['photo_links'] = photo_links[begin:number + begin]

    def click_and_scrape_captions(self, number):
        print('Scraping captions...')
        captions = []

        for post_num in range(number):
            sys.stdout.write('\033[F')
            print(f'Scraping captions {post_num+1} / {number}')
            if post_num == 0:
                self._driver.find_element_by_xpath(
                    FIREFOX_FIRST_POST_PATH).click()
                if number != 1:
                    WebDriverWait(self._driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, CSS_RIGHT_ARROW))
                    )
            elif number != 1:
                url_before = self._driver.current_url
                self._driver.find_element_by_css_selector(CSS_RIGHT_ARROW).click()

                try:
                    WebDriverWait(self._driver, 10).until(
                        UrlChange(url_before)
                    )
                except TimeoutException:
                    print('Time out in caption scraping at number {post_num}.')
                    break

            try:
                time_element = WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'time'))
                )
                caption = time_element.find_element_by_xpath(TIME_TO_CAPTION_PATH).text
            except NoSuchElementException:
                print(f'Caption not fount in the {post_num} photo')
                caption = ''

            captions.append(caption)

        self._data['captions'] = captions

    def scrape_followers_or_following(self, crawl_type, query, number):
        print(f'Scraping {crawl_type}')
        if crawl_type == 'followers':
            FOLLOW_ELE = CSS_FOLLOWERS
            FOLLOW_PATH = FOLLOWER_PATH
        elif crawl_type == 'following':
            FOLLOW_ELE = CSS_FOLLOWING
            FOLLOW_PATH = FOLLOWING_PATH

        follow_ele = WebDriverWait(self._driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, FOLLOW_ELE.forat(query)))
        )

        if number is 0:
            number = int(filter(str.isdigit, str(follow_ele.text)))
            print('getting all ' + str(number) + ' items')

        follow_ele.click()

        title_ele = WebDriverWait(self._driver, 5).until(
            EC.presence_of_element_located((By.XPATH, FOLLOW_PATH))
        )
        List = title_ele.find_element_by_xpath('..').find_element_by_tag_name('ul')
        List.click()

        num_of_shown_follow = len(List.find_elements_by_xpath('*'))
        while len(List.find_elements_by_xpath('*')) < number:
            element = List.find_elements_by_xpath('*')[-1]

            try:
                element.send_keys(Keys.PAGE_DOWN)
            except Exception as e:
                time.sleep(0.1)

        follow_items = []
        for ele in List.find_elements_by_xpath('*')[:number]:
            follow_items.append(ele.text.split('\n')[0])

        self._data[crawl_type] = follow_items

    def download_and_save(self, dir_prefix, query, crawl_type):
        dir_name = query.lstrip('#') + '.hashtag' if query.startswith('#') else query

        dir_path = os.path.join(dir_prefix, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        print(f'Saving to directory: {dir_path}')

        for idx, photo_link in enumerate(self._data['photo_links'], 0):
            sys.stdout.write('\033[F')
            print(f'Downloading {idx+1} images to ')
            _, ext = os.path.splitext(photo_link)
            filename = str(idx) + ext
            filepath = os.path.join(dir_path, filename)
            urlretrieve(photo_link, filepath)

        for idx, caption in enumerate(self._data['captions'], 0):
            filename = str(idx) + '.txt'
            filepath = os.path.join(dir_path, filename)

            with codecs.open(filepath, 'w', encoding='utf-8') as fout:
                fout.write(caption + '\n')

        filename = crawl_type + '.txt'
        filepath = os.path.join(dir_path, filename)
        if len(self._data[crawl_type]):
            with codecs.open(filepath, 'w', encoding='utf-8') as fout:
                for fol in self._data[crawl_type]:
                    fout.write(fol + '\n')


def main():
    parser = argparse.ArgumentParser(description='Instagram Crawler')
    parser.add_argument('-d', '--dir_prefix', type=str,
                        default='./data/', help='directory to save results')
    parser.add_argument('-q', '--query', type=str, default='instagram',
                        help="target to crawl, add '#' for hastags")
    parser.add_argument('-t', '--crawl_type', type=str, default='photos',
                        help="Options: 'photos' | 'followers' | 'following'")
    parser.add_argument('-n', '--number', type=int, default=0,
                        help='Number of posts to download: integer')
    parser.add_argument('-c', '--caption', action='store_true',
                        help='Add this flag to download caption when downloading photos')
    parser.add_argument('-l', '--headless', action='store_true',
                        help='If set, will use PhantomJS driver to run script as headless')
    parser.add_argument('-a', '--authentication', type=str, default=None,
                        help='path to authentication json file')
    parser.add_argument('-f', '--firefox_path', type=str, default=None,
                        help='path to Firefox installation')
    args = parser.parse_args()

    crawler = InstagramCrawler(headless=args.headless, firefox_path=args.firefox_path)
    crawler.crawl(dir_prefix=args.dir_prefix,
                  query=args.query,
                  crawl_type=args.crawl_type,
                  number=args.number,
                  caption=args.caption,
                  authentication=args.authentication)


if __name__ == '__main__':
    main()
