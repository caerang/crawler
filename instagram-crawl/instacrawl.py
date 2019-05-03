# Copyright 2019, Hyeongdo Lee. All Rights Reserved.
# 
# e-mail: mylovercorea@gmail.com
#
# ==============================================================================
"""
"""
from builtins import open

import argparse
import glob
import json
import os
import sys
import time
from io import open
from browser import Browser
import secret
from exceptions import RetryException
from utils import retry
from tqdm import tqdm
from time import sleep
from downloader import download_images


class Logging:
    PREFIX = 'instagram-crawler'

    def __init__(self):
        try:
            timestamp = int(time.time())
            self.cleanup(timestamp)
            self.logger = open(f'/tmp/{Logging.PREFIX}-{timestamp}.log', 'w')
            self.log_disable = False
        except Exception:
            self.log_disable = True

    def cleanup(self, timestamp):
        days = 86400 * 7
        days_ago_log = f'/tmp/{Logging.PREFIX}-{timestamp - days}'
        for log in glob.glob('/tmp/instagram-crawler-*.log'):
            if log < days_ago_log:
                os.remove(log)

    def log(self, msg):
        if self.log_disable:
            return

        self.logger.write(msg + '\n')
        self.logger.flush()

    def __del__(self):
        if self.log_disable:
            return
        self.logger.close()


class InsCrawler(Logging):
    URL = 'https://www.instagram.com'
    RETRY_LIMIT = 10

    def __init__(self, has_screen=False):
        super(InsCrawler, self).__init__()
        self.browser = Browser(has_screen)
        self.page_height = 0

    def _dismiss_login_prompt(self):
        ele_login = self.browser.find_one('.Ls00D .Szr5J')
        if ele_login:
            ele_login.click()

    def _get_posts(self, number):
        TIMEOUT = 600
        browser = self.browser
        key_set = set()
        posts = []
        pre_post_num = 0
        wait_time = 1

        pbar = tqdm(total=number)

        def start_fetching(pre_post_num, wait_time):
            ele_posts = browser.find('.v1Nh3 a')
            for ele in ele_posts:
                key = ele.get_attribute('href')
                if key not in key_set:
                    ele_img = browser.find_one('.KL4Bh img', ele)
                    caption = ele_img.get_attribute('alt')
                    img_url = ele_img.get_attribute('src')
                    key_set.add(key)
                    posts.append({
                        'key': key,
                        'caption': caption,
                        'img_url': img_url
                    })
            if pre_post_num == len(posts):
                pbar.set_description(f'Wait for {wait_time} set')
                sleep(wait_time)
                pbar.set_description('fetching')

                wait_time *= 2
                browser.scroll_up(300)
            else:
                wait_time = 1

            pre_post_num = len(posts)
            browser.scroll_down()

            return pre_post_num, wait_time

        pbar.set_description('fetching')
        while len(posts) < number and wait_time < TIMEOUT:
            post_num, wait_time = start_fetching(pre_post_num, wait_time)
            pbar.update(post_num - pre_post_num)
            pre_post_num = post_num

            loading = browser.find_one('.W1Bne')
            if (not loading and wait_time > TIMEOUT/2):
                break

        pbar.close()
        print(f'Done. Fetched {min(len(posts), number)} posts.')
        return posts[:number]

    def login(self):
        browser = self.browser
        url = f'{InsCrawler.URL}/accounts/login/'
        browser.get(url)
        u_input = browser.find_one('input[name="username"]')
        u_input.send_keys(secret.username)
        p_input = browser.find_one('input[name="password"]')
        p_input.send_keys(secret.password)

        login_btn = browser.find_one('.L3NKy')
        login_btn.click()

        @retry()
        def check_login():
            if browser.find_one('input[name="username"]'):
                raise RetryException()

        check_login()

    def get_latest_posts_by_tag(self, tag, number):
        url = f'{InsCrawler.URL}/explore/tags/{tag}'
        self.browser.get(url)
        return self._get_posts(number)


def usage():
    return '''
        python crawler.py posts -u cal_foodie -n 100 -o ./output
        python crawler.py posts_full -u cal_foodie -n 100 -o ./output
        python crawler.py profile -u cal_foodie -o ./output
        python crawler.py hashtag -t taiwan -o ./output
        The default number for fetching posts via hashtag is 100.
    '''


def get_posts_by_hashtag(tag, number, debug):
    ins_crawler = InsCrawler(has_screen=debug)
    return ins_crawler.get_latest_posts_by_tag(tag, number)


def download_images_by_hashtag(tag, number, debug):
    ins_crawler = InsCrawler(has_screen=debug)
    posts = ins_crawler.get_latest_posts_by_tag(tag, number)
    download_images(posts, tag)


def arg_required(argv, fields=[]):
    for field in fields:
        if not getattr(argv, field):
            parser.print_help()
            sys.exit()


def output(data, filepath=None):
    out = json.dumps(data, ensure_ascii=False)
    if filepath:
        with open(filepath, 'w', encoding='utf8') as f:
            f.write(out)
    else:
        print(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Instagram Crawler',
                                     usage=usage())
    parser.add_argument('mode', help='options: [hashtag]')
    parser.add_argument('-n', '--number',
                        type=int,
                        help='number of returned posts')
    parser.add_argument('-t', '--tag',
                        help='instagram\'s tag name')
    parser.add_argument('-o', '--output', help='output file name(json format)')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.mode == 'hashtag':
        arg_required('tag')
        # output(get_posts_by_hashtag(args.tag, args.number or 100, args.debug),
        #        args.output)
        download_images_by_hashtag(args.tag, args.number or 100, args.debug)
    else:
        usage()
