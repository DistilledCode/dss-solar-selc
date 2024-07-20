import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Generator, Iterable, Union

import requests
from bs4 import BeautifulSoup

from custom_network import PROXIES, USE_SOCKS
from eec import EECScraper


class SetEncoder(json.JSONEncoder):
    def default(self, obj: Iterable) -> Union[list, Any]:
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def date_range(
    start_date: datetime,
    end_date: datetime,
) -> Generator[any, any, datetime]:
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


class NLEECScraper:
    """
    A scraper for the Economic Times Energy newsletter articles.

    This class provides functionality to scrape and store articles from the
    Economic Times Energy newsletter across various categories. It manages the
    scraping process, handles data storage, and provides methods for fetching
    both newsletters and individual articles.

    Attributes:
        HEADERS (dict): HTTP headers for making requests.
        CATEGORIES (list): List of article categories to scrape.
        ENERGY_BASE (str): Base URL for the Energy section.
        NL_BASE (str): Base URL for newsletters.
        AJAX_CALL_URL (str): URL for AJAX calls.

    Methods:
        fetch_articles(): Fetches articles from categorized newsletter links.
        fetch_newsletters(): Retrieves newsletters for a date range.
        _get_details(article_url): Scrapes details for a single article.
        _load_listing(topic): Loads existing article data for a topic.
        _dump_listing(topic): Saves article data for a topic.
        _load_errors(): Loads list of faulty article IDs.
        _dump_errors(): Saves list of faulty article IDs.
        _load_nletters(): Loads existing newsletter data.
        _dump_nletters(): Saves newsletter data.
        _nl_links_count(): Counts total links in newsletters.
        _categorize_nletters(): Categorizes newsletter links by topic.

    The scraper creates a directory structure to store scraped data:
    - ./dump/scraper/nleec/: Root directory for scraped data
    - newsletter.json: Stores all newsletter data
    - {category}.json: Stores articles for each category
    - errors.json: Stores IDs of articles that couldn't be scraped

    Usage:
        scraper = NLEECScraper()
        scraper.fetch_newsletters()
        scraper.fetch_articles()
    """

    HEADERS = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "DNT": "1",
        "Sec-GPC": "1",
        "Connection": "keep-alive",
        "Referer": "https://energy.economictimes.indiatimes.com/news",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=1",
        "TE": "trailers",
    }
    CATEGORIES = [
        "news%2Fenvironment",
        "news%2Frenewable",
        "news%2Fcompanies",
        "news%2Feconomy",
        "news%2Fpower",
        "news%2Fcoal",
        "news%2Foil",
    ]
    ENERGY_BASE = "https://energy.economictimes.indiatimes.com"
    NL_BASE = url = ENERGY_BASE + "/newsletter?for_date={date}&activity_id=35"
    AJAX_CALL_URL = "https://energy.economictimes.indiatimes.com/ajax/call"

    def __init__(self) -> None:
        """
        Initialize the NLEECScraper.

        Sets up the directory structure for storing scraped data.
        """
        self.scrpdir = Path("./dss-selc-dump/scraper")
        self.scrpdir.mkdir(exist_ok=True, parents=True)
        self.nleecdir = self.scrpdir / "nleec"
        self.nleecdir.mkdir(exist_ok=True, parents=True)
        self.nletter_path = self.nleecdir / "newsletter.json"

    def _load_listing(self, topic: str) -> None:
        """
        Load existing article data for a given topic.

        Args:
            topic (str): The category of articles to load.

        Loads data from a JSON file if it exists,
        otherwise initializes an empty dictionary.
        """

        fp = self.nleecdir / f"{topic}.json"

        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.eec_articles = json.load(file)
            print(f"[*] {len(self.eec_articles)} articles loaded")
        else:
            fp.touch()
            self.eec_articles = {}
            print(f"[*] {fp.name} does not exist, creating one.")

    def _dump_listing(self, topic: str) -> None:
        """
        Save article data for a given topic.

        Args:
            topic (str): The category of articles to save.

        Writes the current article data to a JSON file.
        """

        with open(self.nleecdir / f"{topic}.json", "w") as f:
            json.dump(self.eec_articles, f, indent=4)
        print(f"[*] Dumped {len(self.eec_articles):>04} {topic} articles.")

    def _load_errors(self) -> None:
        """
        Load the list of faulty article IDs.

        Reads from a JSON file if it exists, otherwise initializes an empty list.
        """
        fp = self.nleecdir / "errors.json"
        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.faulty_ids = json.load(file)
            print(f"[*] Loaded {len(self.faulty_ids)} faulty ids")

        else:
            fp.touch()
            self.faulty_ids = []
            print(f"[*] {fp.name} does not exist, creating one.")

    def _dump_errors(self) -> None:
        """
        Save the list of faulty article IDs.

        Writes the current list of faulty IDs to a JSON file.
        """
        fp = self.nleecdir / "errors.json"
        with open(fp, "w") as f:
            json.dump(self.faulty_ids, f, cls=SetEncoder, indent=4)
        print(f"[*] Dumped {len(self.faulty_ids)} faulty ids")

    def _load_nletters(self) -> None:
        """
        Load existing newsletter data.

        Reads from a JSON file if it exists, otherwise initializes an empty dictionary.
        """

        if self.nletter_path.exists():
            print(f"[*] {self.nletter_path.name} exist, loading it.")
            with self.nletter_path.open("r") as file:
                self.nletters = json.load(file)
            print(f"[*] Newsletters of {len(self.nletters)} dates loaded")
            print(f"[*] Total links loaded: {self._nl_links_count()}")

        else:
            self.nletter_path.touch()
            self.nletters = {}
            print(f"[*] {self.nletter_path.name} does not exist, creating one.")

    def _dump_nletters(self) -> None:
        """
        Save newsletter data.

        Writes the current newsletter data to a JSON file.
        """

        with open(self.nletter_path, "w") as f:
            json.dump(self.nletters, f, cls=SetEncoder, indent=4)
        print(
            f"[*] Dumped {self._nl_links_count()} links,"
            f" {len(self.nletters):>04} newsletters"
        )

    def _get_details(self, article_url: str) -> None:
        """
        Scrape details for a single article.

        Args:
            article_url (str): The URL of the article to scrape.

        Fetches the article, extracts its data,
        and stores it in the eec_articles dictionary.
        Handles various exceptions and adds faulty URLs to the faulty_ids list.
        """

        article_id = article_url.split("/")[-1]
        try:
            response = requests.get(
                article_url,
                proxies=PROXIES if USE_SOCKS is True else None,
            )
        except Exception:
            self.faulty_ids.append(article_url)
            return
        if response.status_code != 200:
            print(f"[!] {response.status_code} {article_url=}")
            if response.status_code == 404:
                self.faulty_ids.append(article_id)
                print(
                    f"[!] {article_id} DNE, added to faulty_ids,"
                    f" total faults: {len(self.faulty_ids)}"
                )
            return
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            script_tag = soup.find_all("script", type="application/ld+json")[1]
        except Exception as e:
            print(f"[!] script tag issue: {article_url}, {str(e)}")
            self.faulty_ids.append(f"{article_url}")
            return
        try:
            data = json.loads(script_tag.string)
        except Exception:
            print(f"[!] Decoding Error for {article_url}")
            return
        headline = data.get("headline", "Dummy Headline")
        self.eec_articles.setdefault(article_id, {})
        self.eec_articles[article_id]["data"] = data
        print(f"[*] [{len(self.eec_articles)}] {headline}")

    def _nl_links_count(self) -> int:
        """
        Count the total number of links in all newsletters.

        Returns:
            int: The total count of links across all newsletters.
        """
        return sum(len(v2) for v1 in self.nletters.values() for v2 in v1.values())

    def _categorize_nletters(self) -> dict[str, set[str]]:
        """
        Categorize newsletter links by topic.

        Returns:
            dict: A dictionary with topics as keys and set of article URLs as values.
        """
        self._load_nletters()
        categorized = {}
        for v in self.nletters.values():
            for kk, vv in v.items():
                categorized.setdefault(kk, set())
                categorized[kk].update(set(vv))
        return categorized

    def fetch_articles(self) -> None:
        """
        Fetch articles from categorized newsletter links.

        Iterates through categorized links, checks for existing or faulty articles,
        and scrapes new articles. Periodically saves progress.
        """
        data = self._categorize_nletters()
        for k, v in data.items():
            print(k.ljust(10), len(v))
        time.sleep(5)
        data = {i: data[i] for i in sorted(data.keys(), key=len, reverse=True)}
        self._load_errors()
        for category, articles in data.items():
            scraper = EECScraper()
            scraper._load_listing(category + "-news")
            count = 0
            self._load_listing(category)
            for article_url in articles:
                article_id = article_url.split("/")[-1]
                if article_id in self.eec_articles:
                    print(f"[!] {article_id} already scrapped using NLEECScraper")
                    continue
                if article_id in scraper.eec_articles:
                    print(f"[!] {article_id} already scrapped using EECScraper")
                    continue
                if article_id in self.faulty_ids:
                    print(f"[!] {article_id} is a faulty id, skipping.")
                    continue

                self._get_details(article_url)
                count += 1
                if count % 10 == 0:
                    self._dump_listing(category)
                    self._dump_errors()
            self._dump_errors()
            self._dump_listing(category)

    def fetch_newsletters(self) -> None:
        """
        Retrieve newsletters for a date range.

        Fetches newsletters from 2010-01-01 to two days before the current date.
        Extracts article links from each newsletter and categorizes them.
        Saves progress after processing each date.
        """
        self._load_nletters()
        start_date = datetime(2010, 1, 1)
        end_date = datetime.now() - timedelta(days=2)
        for date in date_range(start_date, end_date):
            frmt_date = date.strftime("%Y-%m-%d")
            if frmt_date in self.nletters:
                print(f"\r[!] {frmt_date} already scrapped, skipping it.", end="")
                continue
            atleast_one = False
            self.nletters[frmt_date] = {i[7:]: set() for i in self.CATEGORIES}
            print(f"[*] Scrapping for {frmt_date}")
            nl_url = NLEECScraper.NL_BASE.format(date=frmt_date)
            response = requests.get(
                url=nl_url,
                proxies=PROXIES if USE_SOCKS is True else None,
            )
            if response.status_code != 200:
                print(f"[*] [{frmt_date}] {response.status_code} {nl_url}")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.find_all("a", href=True):
                for cat in NLEECScraper.CATEGORIES:
                    if cat in anchor["href"]:
                        headline = re.sub(r"\s+", " ", anchor.get_text()).strip()
                        if headline.lower() not in ("", "read more"):
                            print(f"\t[*] {cat[7:].rjust(12)}:", headline)
                            url = (
                                anchor["href"]
                                .partition("?url=")[-1]
                                .partition("&mailer_id")[0]
                            )
                            url = requests.utils.unquote(url)
                            self.nletters[frmt_date][cat[7:]].add(url)
                            atleast_one = True
            if atleast_one is False:
                print(f"\t[?] No newsletter on {frmt_date}? {nl_url}")
                continue
            self.nletters[frmt_date] = {
                k: list(v) for k, v in self.nletters[frmt_date].items()
            }
            self._dump_nletters()
