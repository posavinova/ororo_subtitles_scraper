## Ororo Subtitle Scraper

Ororo Subtitle Scraper is a Python-based tool for crawling and downloading subtitles from the https://ororo.tv/ website. It consists of two main components: a crawler for obtaining links to movies or TV series, and a scraper for downloading and organizing subtitles.

### Installation

- Clone the Ororo Subtitle Scraper repository to your local machine:

```shell
git clone https://github.com/posavinova/ororo_subtitles_scraper.git
cd ororo-subtitles-scraper
```

- Install the required Python packages:

```shell
pip install -r requirements.txt
```

- Download the ChromeDriver executable from https://chromedriver.chromium.org/ and place it in the project directory. Make sure it matches your Chrome browser version.


### Usage

#### Crawler

The crawler component is used to collect links to movies or TV series from the Ororo.TV website.

#### Scraper
The scraper component is responsible for downloading and organizing by seasons and episodes subtitles for the content crawled by the crawler.

---

1) In `constants.py` specify your credentials (login and password for ororo account).
2) In `main.py` pass desired language for downloading subs to `OroroSubtitlesScraper` and type of content to search for to `OroroSeleniumCrawler`.

  - supported languages:
    - en
    - es
    - it
    - de
    - pl
    - pt
    - ru
    - tr
    - fr
    - cs


  - content types:
    - movies
    - shows

3) Run the script
```shell  
python -m main
```
