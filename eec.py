import json
import re
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup


class EECScrapper:
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
    ENERGY_BASE = "https://energy.economictimes.indiatimes.com"
    AJAX_CALL_URL = "https://energy.economictimes.indiatimes.com/ajax/call"

    def __init__(self) -> None:
        """Initialize Scrapper object and create scraper directory"""
        self.scrpdir = Path("./dump/scrapper")
        self.scrpdir.mkdir(exist_ok=True, parents=True)
        self.eecdir = self.scrpdir / "eec"
        self.eecdir.mkdir(exist_ok=True, parents=True)

    def _load_listing(self, topic: str) -> None:
        """
        Load previously scraped articles from JSON file or create new file if not exists

        Args:
            topic (str): Article topic
        """

        fp = self.eecdir / f"{topic}.json"

        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.eec_articles = json.load(file)
            print(f"[*] {len(self.eec_articles)} articles loaded")
            self.first_time = False
        else:
            fp.touch()
            self.first_time = True
            self.eec_articles = {}
            print(f"[*] {fp.name} does not exist, creating one.")

    def _dump_listing(self, topic: str) -> None:
        """
        Save scraped articles to JSON file

        Args:
            topic (str): Article topic
        """

        with open(self.eecdir / f"{topic}.json", "w") as f:
            json.dump(self.eec_articles, f, indent=4)
        print(f"[*] Dumped {len(self.eec_articles):>04} {topic} articles.")

    def _get_meta(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract metadata from a BeautifulSoup object representing an article.

        Args:
            soup (BeautifulSoup): BeautifulSoup object containing article HTML.

        Returns:
            Optional[str]: Article ID if successful, None if article is a duplicate.

        Extracts the headline, URL, and summary from the provided HTML soup
        and adds it to the scraped articles dictionary.
        """
        first_anchor = soup.find("a")
        headline = re.sub(r"\s+", " ", first_anchor.get_text()).strip()
        _url = first_anchor["href"]
        if _url.startswith("/") is False:
            _url = "/" + _url
        url = self.ENERGY_BASE + _url
        summary = re.sub(r"\s+", " ", soup.find("p").get_text()).strip()
        article_id = url.split("/")[-1].partition("?")[0]
        if article_id in self.eec_articles and self.first_time is False:
            print(f"[!] [{len(self.eec_articles):>04}] Duplicate Spotted, exiting.")
            return None
        self.eec_articles[article_id] = {
            "url": url,
            "headline": headline,
            "summary": summary,
        }
        return article_id

    def _get_details(self, article_id: str) -> None:
        """
        Fetch and parse detailed information for a specific article.

        Args:
            article_id (str): Unique identifier for the article.

        Retrieves the full article page, extracts detailed information
        from the JSON-LD script tag, and adds it to the article's data.
        """
        url = self.eec_articles[article_id]["url"]
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[!] {response.status_code} {url=}")
            return
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find_all("script", type="application/ld+json")[1]
        try:
            data = json.loads(script_tag.string)

        except JSONDecodeError:
            print(f"[!] Decoding Error for {article_id}")
            return
        headline = data.get("headline", "Dummy Headline")
        self.eec_articles[article_id]["data"] = data
        print(f"[*] [{len(self.eec_articles)}] {headline}")

    def _get_articles(self, resp_json: dict) -> Optional[bool]:
        """
        Process a JSON response containing multiple articles.

        Args:
            resp_json (dict): JSON response containing article HTML.

        Returns:
            Optional[bool]: True if processing was successful.
                            None if a duplicate was found.

        Parses the HTML in the JSON response, extracts metadata for each article,
        and fetches detailed information for new articles.
        """
        soup = BeautifulSoup(resp_json["html"], "html.parser")
        for article_soup in soup.find_all("li"):
            article_id = self._get_meta(article_soup)
            if article_id is None:
                return None
            self._get_details(article_id)
        return True

    def _get_pararms(self, page_count: int, topic: str) -> dict[str, Any]:
        """
        Generate parameters for API requests based on topic and page number.

        Args:
            page_count (int): Current page number being requested.
            topic (str): Topic of articles to fetch.

        Returns:
            dict[str, Any]: Dictionary of parameters to be used in the API request.

        Constructs the appropriate parameters for different topics and pages
        to be used in API requests.
        """
        param_dict = {
            "renewable-news": "Renewable",
            "oil-news": "oil-and-gas",
            "coal-news": "coal",
            "power-news": "power",
        }

        if topic == "all-news":
            return {
                "module": "RevNewsListing",
                "ajax_params": json.dumps(
                    {
                        "is_ajax": True,
                        "page": page_count,
                    }
                ),
            }
        if topic == "economy-news":
            return {
                "module": "RevTagWiseNewsListing",
                "ajax_params": json.dumps(
                    {
                        "q": "economy",
                        "is_ajax": True,
                        "action": "",
                        "page": page_count,
                    }
                ),
            }
        return {
            "module": "RevCategoryWiseNewsListing",
            "ajax_params": json.dumps(
                {
                    "cat_name": param_dict.get(topic),
                    "sub_cat_name": "",
                    "is_ajax": True,
                    "page": page_count,
                }
            ),
        }

    def fetch_articles(self, topic: str) -> None:
        """
        Main method to fetch articles for a given topic.

        Args:
            topic (str): Topic of articles to fetch.

        Orchestrates the entire scraping process for a given topic,
        including loading existing data, making API requests,
        processing responses, and saving results.
        """
        self._load_listing(topic)
        page_count = 0
        while True:
            page_count += 1
            print(f"[*] Scrapping page {page_count}")
            params = self._get_pararms(page_count, topic)
            response = requests.get(
                self.AJAX_CALL_URL,
                params=params,
                headers=self.HEADERS,
            )
            if response.status_code != 200:
                print(
                    f"[*] [{len(self.eec_articles):>04}] URL: {response.url}\n"
                    f"Status Code: {(response.status_code)}"
                )
                continue
            resp_json = response.json()
            if resp_json["data"]["has_reached_end"] is True:
                print("[!] Reached last page, stopping.")
                break
            if self._get_articles(resp_json) is None:
                return
            self._dump_listing(topic)
        self._dump_listing(topic)
