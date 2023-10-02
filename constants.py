MOVIES = "movies"
TV_SERIES = "shows"
DRIVER_PATH = "chromedriver.exe"
MAIN_SEED_URL = "https://ororo.tv/ru"
SEEDS_PATH = "ororo_seed_urls_to_scrape.csv"
CHECKPOINT_NAME = "last_parsed_url.txt"

LANGUAGES_DICT = {
    "en": "Английские",
    "es": "Испанские",
    "it": "Итальянские",
    "de": "Немецкие",
    "pl": "Польские",
    "pt": "Португальские",
    "ru": "Русские",
    "tr": "Турецкие",
    "fr": "Французские",
    "cs": "Чешские",
}

CREDENTIALS = {
    "login": ...,
    "password": ...
}
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "if-none-match": 'W/"b477619d88c8fadcef2a67a10862f178',
}