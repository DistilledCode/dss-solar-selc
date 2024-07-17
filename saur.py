import json
import re
from pathlib import Path
from time import sleep
from typing import Optional

import requests
from bs4 import BeautifulSoup

from custom_network import PROXIES, USE_SOCKS


class SaurScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        # "Cookie": "og48dbhr=284rlsvaxwwd; a1h4i8n6=kayvqm2t6crw; fvpphomepage23=true",
        "Cookie": "og48dbhr=284rlsvaxwwd; a1h4i8n6=kayvqm2t6crc; fvpphomepage23=true",
        "Referer": "https://www.saurenergy.com/solar-energy-news",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "TE": "trailers",
    }
    SLEEP_TIME = 2.0

    def __init__(self) -> None:
        """Initialize Scraper object and create scraper directory"""
        self.scrpdir = Path("./dss-selc-dump/scraper")
        self.scrpdir.mkdir(exist_ok=True, parents=True)
        self.saurdir = self.scrpdir / "saur"
        self.saurdir.mkdir(exist_ok=True, parents=True)

    def _load_listing(self) -> None:
        fp = self.saurdir / "saur.json"
        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.saur_articles = json.load(file)
            print(f"[*] {len(self.saur_articles):>05} articles loaded")

        else:
            fp.touch()
            self.saur_articles = {}
            print(f"[*] {fp.name} does not exist, creating one.")

    def _dump_listing(self, verbose: bool = True) -> None:
        with open(self.saurdir / "saur.json", "w") as f:
            json.dump(self.saur_articles, f, indent=4)
        if verbose:
            print(f"[*] Dumped {len(self.saur_articles):>05} Saur articles.")

    def _get_body(self, url: str) -> dict[str, Optional[str]]:
        sleep(SaurScraper.SLEEP_TIME)
        response = requests.get(
            url,
            proxies=PROXIES if USE_SOCKS is True else None,
        )
        if response.status_code != 200:
            print(
                f"[!] [{len(self.saur_articles):>05}] {response.status_code=}"
                f"No article body for {url}"
            )
            return {"body": None, "key_words": None}
        soup = BeautifulSoup(response.text, "html.parser")
        try:
            paras = soup.find("div", class_="entry-content clearfix").find_all("p")
        except Exception:
            return {"body": None, "key_words": None}
        body = "\n".join(para.get_text() for para in paras)
        tags = soup.find("div", class_="entry-tags")
        try:
            kws = [i.get_text() for i in tags.find_all("a")]
        except Exception:
            kws = []
        return {"body": re.sub(r"\s+", " ", body).strip(), "key_words": kws}

    def _add_articles(self, response: requests.Response) -> None:
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article")
        if not articles:
            print("[?] No articles found, exiting")
            return False
        for article in articles:
            _id = article["id"]
            if _id in self.saur_articles:
                print(f"\t[*] {_id} already scraped.")
                print("\t[!] List is upto date, exiting.")
                return False
            anchor = article.find("a", class_="content-title-link")
            title = re.sub(r"\s+", " ", anchor.get_text(strip=True)).strip()
            url = anchor["href"]
            date_published = article.find("span", itemprop="datePublished").get_text()
            author = article.find("span", class_="vcard author").get_text(strip=True)
            summary = (
                article.find("div", class_="entry-summary content-list-summary")
                .find("p")
                .get_text(strip=True)
            )
            article_dict = {
                "article_id": _id,
                "url": url,
                "title": title,
                "date_published": re.sub(r"\s+", " ", date_published).strip(),
                "author": re.sub(r"\s+", " ", author).strip(),
                "summary": re.sub(r"\s+", " ", summary).strip(),
            }
            self.saur_articles[_id] = article_dict
            print(
                f"\t[*] [{len(self.saur_articles):>05}] "
                f"[{article_dict['date_published']}] "
                f"{article_dict['title']}"
            )
        return True

    def fetch_body(self) -> None:
        self._load_listing()
        for ind, (k, v) in enumerate(self.saur_articles.items(), start=1):
            if v.get("body") is not None:
                print(f"[*] [{ind:>05}] Body for {k} already exist.")
                continue
            self.saur_articles[k] |= self._get_body(v["url"])
            print(f"[*] [{ind:>05}] fetched body for {k}")
            self._dump_listing(verbose=False)
        self._dump_listing(verbose=False)

    def fetch_articles(self) -> None:
        self._load_listing()
        page_num = 1
        # page_num = len(self.saur_articles) // 9 + 1
        while True:
            requrl = f"https://www.saurenergy.com/solar-energy-news/page/{page_num}"
            print(f"[*] Page Num = {page_num}")
            sleep(SaurScraper.SLEEP_TIME)
            response = requests.get(
                url=requrl,
                headers=SaurScraper.HEADERS,
                proxies=PROXIES if USE_SOCKS is True else None,
            )
            if response.status_code != 200:
                print(
                    f"[!] [{len(self.saur_articles):>05}] "
                    f"{page_num=} {response.status_code=}"
                )
                continue
            if self._add_articles(response) is False:
                print("[?] Probably reached EOL, exiting.")
                break
            self._dump_listing()
            page_num += 1
        self._dump_listing()
