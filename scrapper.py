import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup


class ECScrapper:
    EC_URL = "https://economictimes.indiatimes.com/"
    EC_LL = EC_URL + "defencelazyloadinglist/cfmid-"
    EC_CMFID_URL = {
        "solar": EC_LL + "4005094.cms?curpg={pg}&msid=81585238",
        "renewable-regulation": EC_LL + "4016096.cms?curpg={pg}&msid=81585238",
        "hybrid": EC_LL + "4005093.cms?curpg={pg}&msid=81585238",
    }
    HEADERS = {
        "User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers",
    }

    def __init__(self) -> None:
        """Initialize Scrapper object and create scraper directory"""
        self.scrpdir = Path("./dump/scrapper")
        self.scrpdir.mkdir(exist_ok=True, parents=True)

    def _get_article_meta(self, soup: BeautifulSoup) -> Optional[dict[str, str]]:
        """
        Extract article metadata from BeautifulSoup object

        Args:
            soup (BeautifulSoup): Parsed HTML of an article listing

        Returns:
            Optional[dict[str, str]]: Article metadata (title, URL) or None if not found
        """

        anchor = soup.find("a", class_=["anc", "ancs"])
        if anchor is not None:
            title = anchor["title"]
            url = anchor["href"]
            return {"title": title, "url": url}
        return None

    def _get_article_details(self, url: str) -> Optional[dict[str, Any]]:
        """
        Fetch full article details from given URL

        Args:
            url (str): Article URL

        Returns:
            Optional[dict[str, Any]]: Full article details or None if error

        Raises:
            JSONDecodeError: If the JSON data in script tag cannot be parsed
        """

        resp = requests.get(
            url=ECScrapper.EC_URL + url,
            headers=ECScrapper.HEADERS,
        )
        if resp.status_code != 200:
            print(f"[!] {resp.status_code} Error fetching article: {url}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        script_tag = soup.find_all("script", type="application/ld+json")[1]
        try:
            details = script_tag.string.replace("\n", "").replace("\t", "")
            data = json.loads(details)
        except JSONDecodeError:
            print(repr(script_tag.string))
            raise
        headline = data.get("headline", "Headline DNE")
        print(f"[*] [{len(self.ec_articles)+1}] {headline}")
        return data

    def _get_article_listings(self, soup: BeautifulSoup) -> bool:
        """
        Extract article listings from BeautifulSoup object and add to self.ec_articles

        Args:
            soup (BeautifulSoup): Parsed HTML of page with article listings

        Returns:
            bool: True if soup had at least one new listing,
                False if no listings or only duplicates
        """
        article_listings = soup.find_all("li")
        if len(article_listings) == 0:
            print("[!] Reached EOL. Scrapping Done.")
            return False

        for element in article_listings:
            if (meta := self._get_article_meta(element)) is None:
                print("[!] Error in extracting metadata.")
                continue
            article_id = meta["url"].split("/")[-1].split(".")[0]
            if article_id in self.ec_articles:
                print("[!] Duplicate Spotted. List is upto date. Exiting")
                return False
            article_detail = self._get_article_details(meta["url"])
            if article_detail is None:
                print("[!] Error in extracting details.")
                continue
            self.ec_articles[article_id] = article_detail
        return True

    def _dump_listing(self, topic: str) -> None:
        """
        Save scraped articles to JSON file

        Args:
            topic (str): Article topic
        """

        with open(self.ecdir / f"{topic}.json", "w") as f:
            json.dump(self.ec_articles, f, indent=4)
        print(f"[*] Dumped {len(self.ec_articles):>04} {topic} articles.")

    def _load_listing(self, topic: str) -> None:
        """
        Load previously scraped articles from JSON file or create new file if not exists

        Args:
            topic (str): Article topic
        """

        fp = self.ecdir / f"{topic}.json"

        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.ec_articles = json.load(file)
            print(f"[*] {len(self.ec_articles)} articles loaded")
        else:
            fp.touch()
            self.ec_articles = {}
            print(f"[*] {fp.name} does not exist, creating one.")

    def fetch_ec(self, topic: str) -> None:
        """
        Main method to scrape articles for a given topic

        Args:
            topic (str): Article topic to scrape
        """
        self.ecdir = self.scrpdir / "ec"
        self.ecdir.mkdir(exist_ok=True, parents=True)
        self._load_listing(topic)
        cmfid_url = ECScrapper.EC_CMFID_URL.get(topic)
        page_count = 0
        while True:
            page_count += 1
            requrl = cmfid_url.format(pg=page_count)
            response = requests.get(requrl, headers=ECScrapper.HEADERS)
            if response.status_code != 200:
                print(
                    f"[*] [{len(self.ec_articles):>04}] URL: {response.url}\n"
                    f"Status Code: {(response.status_code)}"
                )
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            if self._get_article_listings(soup) is False or None:
                break
            self._dump_listing(topic)
        self._dump_listing(topic)
