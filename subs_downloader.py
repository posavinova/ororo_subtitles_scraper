import logging
import re
import shutil
from pathlib import Path
from typing import List, Dict, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import HEADERS, LANGUAGES_DICT, SEEDS_PATH, CHECKPOINT_NAME, MOVIES, TV_SERIES

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class InvalidArgumentError(Exception):
    """
    Cannot process the arguments
    """


class OroroSubtitlesScraper:
    def __init__(self, data_to_scrape: str, language: str, cookies: Dict[str, str]) -> None:
        """
        :param self:
        :param data_to_scrape: **"movies"** | **"shows"**
        :param language: **"en"** | **"es"** | **"it"** | **"de"** | **"pl"** | **"pt"** | **"ru"** | **"tr"** | **"fr"** | **"cs"**
        :return: None
        """
        self.data_to_scrape = data_to_scrape if data_to_scrape in [MOVIES, TV_SERIES] else None
        self.language = language if language in LANGUAGES_DICT else None
        self.cookies = cookies
        if self.data_to_scrape is None or self.language is None:
            raise InvalidArgumentError
        self.seed = ""
        log.info(f"Initialized {self.language} subtitles {self.data_to_scrape} scraper")

    def set_seed(self) -> None:
        seed_file_path = Path(__file__).parent / CHECKPOINT_NAME
        if not seed_file_path.exists():
            self.seed = ""
        else:
            with open(seed_file_path) as saved_seed:
                self.seed = saved_seed.readline()

    @staticmethod
    def update_seed(next_link: str) -> None:
        seed_file_path = Path(__file__).parent / CHECKPOINT_NAME
        with open(seed_file_path, "w") as new_seed:
            new_seed.write(next_link)

    def get_seeds(self) -> List[str]:
        seeds = pd.read_csv(SEEDS_PATH)["films_links"].to_list()

        if not self.seed:
            return seeds
        last_seed_idx = seeds.index(self.seed)
        seeds = seeds[last_seed_idx + 1:]
        return seeds

    def download_subs(self, url: str, path: Path) -> None:
        try:
            response = requests.get(
                "https://ororo.tv/" + url, headers=HEADERS, cookies=self.cookies
            )
            response.raise_for_status()
            with open(path, "wb") as file:
                file.write(response.content)
        except requests.RequestException as e:
            log.error(f"Could not download subtitles: {str(e)}")

    @staticmethod
    def save_meta(meta: Dict[str, Union[str, None]], path: Path) -> None:
        table = pd.DataFrame(meta, index=[0])
        table.to_csv(path, mode="a", header=not path.exists())

    def _contains_subs(self, link: str) -> bool:
        try:
            response = requests.get(
                link, headers=HEADERS, cookies=self.cookies, timeout=15
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, features="lxml")
            sub_lang = LANGUAGES_DICT.get(self.language)
            right_subs = soup.select(f'a[title*="Скачать {sub_lang} субтитры"]')
            return bool(right_subs)
        except Exception as e:
            log.error(f"Error checking for subtitles: {str(e)}")
            return False

    def scrape(self) -> None:
        self.set_seed()
        for link in tqdm(self.get_seeds()):
            try:
                if not self._contains_subs(link):
                    log.info(f"Skipping page {link}. No subs for the required language.")
                    continue
                else:
                    log.info(f"Fetching page {link}.")
                    response = requests.get(
                        link, headers=HEADERS, cookies=self.cookies, timeout=15
                    )
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, features="lxml")

                    sub_lang = LANGUAGES_DICT.get(self.language)

                    film_name = re.search(
                        rf"(?<=ororo\.tv/ru/{self.data_to_scrape}/).+", link
                    ).group()
                    assets_path = (
                            Path(__file__).parent
                            / f"{self.data_to_scrape}_subtitles_{self.language}"
                            / f"{film_name}"
                    )
                    shutil.rmtree(assets_path, ignore_errors=True)
                    Path(assets_path).mkdir(parents=True, exist_ok=True)

                    fields = soup.select("span.field-name")
                    for field in fields:
                        field.decompose()

                    title = soup.select_one("div.show-content__title")
                    description = soup.select_one("div.show-content__description")
                    rating = soup.select_one("div#rating")
                    year = soup.select_one("div#year")
                    genres = soup.select_one("div#genres")
                    countries = soup.select_one("div#countries")
                    length = soup.select_one("div#length")
                    status = soup.select_one("div#status")
                    img = soup.select_one("img.poster-image")
                    text_values = [
                        title,
                        description,
                        rating,
                        year,
                        genres,
                        countries,
                        length,
                        status,
                    ]
                    meta_values = [
                        value.text.strip() if value else None
                        for value in text_values
                    ]
                    if img:
                        meta_values.append(img["src"])
                    else:
                        meta_values.append(None)

                    meta_keys = [
                        "title",
                        "description",
                        "rating",
                        "year",
                        "genres",
                        "countries",
                        "length",
                        "status",
                        "img",
                    ]

                    metadata = {
                        key: value for key, value in zip(meta_keys, meta_values)
                    }

                    if not (
                            meta_path := assets_path / f"{film_name}_meta.csv"
                    ).exists():
                        self.save_meta(metadata, meta_path)

                    if self.data_to_scrape == TV_SERIES:
                        seasons = soup.select("div.tab-pane.js-season-tab")
                        seasons_nums = [season["id"] for season in seasons]

                        for season, seasons_num in zip(seasons, seasons_nums):
                            Path(assets_path / f"S{seasons_num}").mkdir(
                                parents=True, exist_ok=True
                            )
                            episodes = [
                                available_episode for available_episode
                                in season.select(
                                    "ul li.show-content__episode-row.js-episode-wrapper.js-media-wrapper"
                                )
                                if not available_episode.select("div.locked-icon")
                            ]
                            for episode in episodes:
                                if link_to_subs := episode.select_one(
                                        f'a[title*="Скачать {sub_lang} субтитры"]'
                                ):
                                    episode_num = (
                                        episode.select_one(
                                            "div.show-content__episode-num.js-num-episode"
                                        )
                                        .text.strip()
                                        .split("\n")[0]
                                    )
                                    if not (
                                            ep_path := assets_path
                                                       / f"S{seasons_num}"
                                                       / f"EP{episode_num}.srt"
                                    ).exists():
                                        self.download_subs(
                                            url=link_to_subs["href"],
                                            path=ep_path
                                        )

                    elif self.data_to_scrape == MOVIES:
                        if link_to_subs := soup.select_one(f'a[title*="Скачать {sub_lang} субтитры"]'):
                            self.download_subs(
                                url=link_to_subs["href"],
                                path=assets_path / f"{film_name}.srt"
                            )
                        else:
                            log.error(f"No subtitles found on page {link}")
                    else:
                        log.error(f"Data type to scrape is not recognized")

                    self.update_seed(link)
                    log.info(f"Page {link} is processed")

            except Exception as e:
                log.error(f"An error occurred: {str(e)}")

        # delete checkpoint file after the spider closes
        (Path(__file__).parent / CHECKPOINT_NAME).unlink()
        for item in (
                Path(__file__).parent.parent / f"subtitles_{self.language}_2023"
        ).iterdir():
            for file in item.iterdir():
                # remove empty seasons
                if file.is_dir():
                    if len(list(file.iterdir())) == 0:
                        shutil.rmtree(file)
