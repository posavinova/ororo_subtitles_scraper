import logging
import pathlib
import re

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from constants import DRIVER_PATH, MAIN_SEED_URL, CREDENTIALS, SEEDS_PATH

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class OroroSeleniumCrawler:
    def __init__(self, data_to_crawl: str) -> None:
        """
        :param self:
        :param data_to_crawl: **"movies"** | **"shows"**
        :return: None
        """
        self.data_to_crawl = data_to_crawl
        self.films_links: list[str] = []
        self.cookies = {}

        log.info(f"Initialized {self.data_to_crawl} crawler")

    def get_films_links(self) -> list[str]:
        return self.films_links

    def set_films_links(self, new_links: list[str]) -> None:
        self.films_links.extend(
            [link for link in new_links if link not in self.get_films_links()]
        )

    @staticmethod
    def _driver_init() -> webdriver.Chrome:
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
        log.info("Initialized webdriver")
        return driver

    @staticmethod
    def _authenticate(driver: webdriver.Chrome) -> None:
        try:
            login = driver.find_element(by=By.LINK_TEXT, value="Войти")
            login.click()

            driver.implicitly_wait(10)

            email = driver.find_element(by=By.ID, value="user_email")
            email.send_keys(CREDENTIALS.get("login"), "")

            password = driver.find_element(by=By.ID, value="user_password")
            password.send_keys(CREDENTIALS.get("password"), "")

            sign_in_button = driver.find_element(by=By.NAME, value="commit")
            sign_in_button.click()

            driver.implicitly_wait(10)
        except Exception as e:
            log.error(f"Authentication failed: {str(e)}")

    def _fetch_films_page(self, driver: webdriver.Chrome) -> None:
        try:
            link_to_films = driver.find_element(
                by=By.CSS_SELECTOR, value=f"a.menu-link[href*='/{self.data_to_crawl}']"
            )
            driver.execute_script("arguments[0].click();", link_to_films)
            driver.implicitly_wait(15)
        except Exception as e:
            log.error(f"Failed to fetch {self.data_to_crawl} page: {str(e)}")

    def save_films_list(self) -> None:
        table = pd.DataFrame(self.get_films_links(), columns=["films_links"])
        table.to_csv(SEEDS_PATH, index=False)

    @staticmethod
    def _if_crawl(seeds_path: str) -> bool:
        if pathlib.Path(seeds_path).exists() and pd.read_csv(seeds_path).films_links.values.any():
            return False
        return True

    def crawl(self) -> None:
        driver = self._driver_init()
        try:
            driver.get(MAIN_SEED_URL)

            # Authentication
            self._authenticate(driver)
            self.cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
            log.info("Logged in successfully")

            if not self._if_crawl(SEEDS_PATH):
                log.info("List of URLs already exists. Skipping crawling.")
                return

            # Go to TV-films or Movies page
            self._fetch_films_page(driver)
            log.info(f"Fetched {self.data_to_crawl} page")

            n_films_element = driver.find_element(By.CSS_SELECTOR, "div.media-count")

            n_films = None
            if n_films_element:
                n_films = int(re.search(r"\d+", n_films_element.text).group())

            if n_films is None:
                log.info(f"Cannot get the number of available {self.data_to_crawl}")
            else:
                log.info(f"There are {n_films} {self.data_to_crawl} available")

            # Initialize a variable to keep track of the number of fetched objects
            fetched_objects = 0

            # Scroll down until the last show is displayed
            while fetched_objects < n_films:
                try:
                    links = [card.get_attribute("href") for card in
                             driver.find_elements(By.CSS_SELECTOR, "div.card-head a")]
                    self.set_films_links(links)
                    self.save_films_list()
                    fetched_objects = len(self.get_films_links())
                    log.info(f"Fetched {fetched_objects} objects")
                    driver.execute_script("window.scrollBy(0, 1080)")
                    driver.implicitly_wait(10)
                except StaleElementReferenceException:
                    log.warning("Stale element reference encountered. Retrying...")
                    continue

            log.info("Crawling completed successfully")
        except Exception as e:
            log.error(f"An error occurred: {str(e)}")
        finally:
            driver.quit()
            log.info(f"Closing crawler.")
