import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from .objects import Scraper
# from .person import Person
import time
import os

class PeopleSearch(object):
    def __init__(self, search_url, driver):
        self.driver = driver
        self.search_url = search_url

    def __find_element_by_xpath__(self, tag_name):
        try:
            self.driver.find_element_by_xpath(tag_name)
            return True
        except:
            pass
        return False

    def get_people(self):
        list_css = 'search-results__list'
        next_xpath = '//button[@aria-label="Next"]'
        driver = self.driver
        driver.get(self.search_url)
        while True:
            try:
                _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, list_css)))
            except:
                # item not found (maybe an empty search result)
                return

            # scroll to draw the page completely out
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/4));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/3));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*2/3));")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)


            # search_results = driver.find_elements_by_class_name("search-result__result-link")
            search_results = driver.find_elements_by_class_name("search-result__info")
            for search_item in search_results:
                _ = WebDriverWait(driver, 10).until(EC.visibility_of(search_item))
                result_link = search_item.find_element_by_class_name("search-result__result-link")
                name = None
                href = None
                try:
                    name = result_link.find_element_by_class_name("name").text.strip()
                    href = result_link.get_property("href")
                except:
                    # most likely a "LinkedIn Member" entry
                    continue

                title_and_company = None
                try: 
                    title_and_company = search_item.find_element_by_class_name("subline-level-1").find_element_by_tag_name('span').text.strip()
                except:
                    pass

                yield (name, title_and_company, href)

            if self.__find_element_by_xpath__(next_xpath) and driver.find_element_by_xpath(next_xpath).is_enabled():
                driver.find_element_by_xpath(next_xpath).click()
            else:
                break
