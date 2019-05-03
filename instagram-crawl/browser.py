# Copyright 2019, Hyeongdo Lee. All Rights Reserved.
# 
# e-mail: mylovercorea@gmail.com
#
# ==============================================================================
"""
"""
import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from utils import randomized_sleep


class Browser:
    def __init__(self, has_screen):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        service_args = ['--ignore-ssl-errors=true']
        chrome_options = Options()
        if not has_screen:
            chrome_options.headless = True
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(
            executable_path=f'{dir_path}/bin/chromedriver'
        )

    def __del__(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def get(self, url):
        self.driver.get(url)

    def find(self, css_selector, elem=None, wait_time=0):
        obj = elem or self.driver

        if wait_time:
            WebDriverWait(obj, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

        try:
            return obj.find_elements(By.CSS_SELECTOR, css_selector)
        except NoSuchElementException:
            return None

    def find_one(self, css_selector, elem=None, wait_time=0):
        obj = elem or self.driver

        if wait_time:
            WebDriverWait(obj, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

        try:
            return obj.find_element(By.CSS_SELECTOR, css_selector)
        except NoSuchElementException:
            return None

    def scroll_down(self, wait=0.3):
        self.driver.execute_script(
            'window.scrollTo(0, document.body.scrollHeight)'
        )
        randomized_sleep(wait)

    def scroll_up(self, offset=-1, wait=2):
        if offset == -1:
            self.driver.execute_script('window.scrollTo(0, 0')
        else:
            self.driver.execute_script(f'window.scrollBy(0, {offset})')
        randomized_sleep(wait)
