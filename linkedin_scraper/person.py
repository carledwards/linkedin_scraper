import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .functions import time_divide
from .objects import Experience, Education, Scraper
import os

class Person(Scraper):
    __TOP_CARD = "pv-top-card"
    name = None
    experiences = []
    educations = []
    location = None
    also_viewed_urls = []
    linkedin_url = None

    def __init__(self, linkedin_url=None, name=None, experiences=[], educations=[], driver=None, get=True, scrape=True, close_on_complete=True):
        self.linkedin_url = linkedin_url
        self.name = name
        self.experiences = experiences or []
        self.educations = educations or []

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(os.path.dirname(__file__), 'drivers/chromedriver')
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete=close_on_complete)


    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_education(self, education):
        self.educations.append(education)

    def add_location(self, location):
        self.location=location
    
    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete = close_on_complete)
        else:
            self.scrape_not_logged_in(close_on_complete = close_on_complete)

    def get_position_details(self, root):
        from_date, to_date, duration = ("Unknown", "Unknown", "Unknown")
        location = None
        position_title = root.find_element_by_tag_name("h3").text.strip()

        try:
            times = root.find_element_by_class_name("pv-entity__date-range").text.strip()
            times = "\n".join(times.split("\n")[1:])
            from_date, to_date, duration = time_divide(times)
        except:
            pass
        try:
            # remove the prefix word "Location\n" from the text
            location = root.find_element_by_class_name("pv-entity__location").text.strip().split('\n')[1]
        except:
            pass
        return (position_title, from_date, to_date, duration, location)

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        root = driver.find_element_by_class_name(self.__TOP_CARD)
        self.name = root.find_elements_by_xpath("//section/div/div/div/*/li")[0].text.strip()

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")

        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "experience-section")))

        # get experience
        exp = driver.find_element_by_id("experience-section")
        for position in exp.find_elements_by_class_name("pv-position-entity"):
            roles = position.find_elements_by_class_name("pv-entity__role-details")
            if len(roles) > 0:
                # person had more than one role at the company
                try:
                    # remove the "Company Name\n" prefix
                    company = position.find_element_by_tag_name("h3").text.strip().split('\n')[1]
                except:
                    company = None

                try:
                    company_website = position.find_element_by_tag_name("a").get_attribute('href')
                except:
                    company_website = None

                # person had multiple roles in the same company
                for role in roles:
                    position_title, from_date, to_date, duration, location = self.get_position_details(role)
                    experience = Experience( position_title = position_title , from_date = from_date , to_date = to_date, duration = duration, location = location)
                    experience.institution_name = company
                    experience.website = company_website
                    self.add_experience(experience)
            else:
                # person had one role
                try:
                    company = position.find_element_by_class_name("pv-entity__secondary-title").text.strip()
                except:
                    company = None

                try:
                    company_website = position.find_element_by_tag_name("a").get_attribute('href')
                except:
                    company_website = None

                position_title, from_date, to_date, duration, location = self.get_position_details(position)
                experience = Experience( position_title = position_title , from_date = from_date , to_date = to_date, duration = duration, location = location)
                experience.institution_name = company
                experience.website = company_website
                self.add_experience(experience)
        
        # get location
        location = driver.find_element_by_class_name(f'{self.__TOP_CARD}--list-bullet')
        location = location.find_element_by_tag_name('li').text
        self.add_location(location)

        driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));")

        _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "education-section")))

        # get education
        edu = driver.find_element_by_id("education-section")
        for school in edu.find_elements_by_class_name("pv-education-entity"):
            university = school.find_element_by_class_name("pv-entity__school-name").text.strip()
            degree = "Unknown Degree"
            try:
                degree = school.find_element_by_class_name("pv-entity__degree-name").text.strip()
                times = school.find_element_by_class_name("pv-entity__dates").text.strip()
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date = ("Unknown", "Unknown")
            education = Education(from_date = from_date, to_date = to_date, degree=degree)
            education.institution_name = university
            self.add_education(education)

        if close_on_complete:
            driver.close()


    def scrape_not_logged_in(self, close_on_complete=True, retry_limit=10):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1


        # get name
        self.name = driver.find_element_by_id("name").text.strip()

        # get experience
        exp = driver.find_element_by_id("experience")
        for position in exp.find_elements_by_class_name("position"):
            position_title = position.find_element_by_class_name("item-title").text.strip()
            company = position.find_element_by_class_name("item-subtitle").text.strip()

            try:
                times = position.find_element_by_class_name("date-range").text.strip()
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date, duration = (None, None, None)

            try:
                location = position.find_element_by_class_name("location").text.strip()
            except:
                location = None
            experience = Experience( position_title = position_title , from_date = from_date , to_date = to_date, duration = duration, location = location)
            experience.institution_name = company
            self.add_experience(experience)

        # get education
        edu = driver.find_element_by_id("education")
        for school in edu.find_elements_by_class_name("school"):
            university = school.find_element_by_class_name("item-title").text.strip()
            degree = school.find_element_by_class_name("original").text.strip()
            try:
                times = school.find_element_by_class_name("date-range").text.strip()
                from_date, to_date, duration = time_divide(times)
            except:
                from_date, to_date = (None, None)
            education = Education(from_date = from_date, to_date = to_date, degree=degree)
            education.institution_name = university
            self.add_education(education)

        # get
        if close_on_complete:
            driver.close()

    def __repr__(self):
        return "{name}\n\nExperience\n{exp}\n\nEducation\n{edu}".format(name = self.name, exp = self.experiences, edu = self.educations)
