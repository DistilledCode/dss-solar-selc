import json
import re
from time import sleep
from typing import Optional
from uuid import NAMESPACE_DNS, uuid5

import requests
from bs4 import BeautifulSoup

from dss_selc.utils import DUMP_PATH, PROXIES, USE_SOCKS


class PvMagUSAScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0)",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Cookie": "c4YGUxxz5aNu6NODlhMDg=hello",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Priority": "u=0, i",
        "TE": "trailers",
    }
    SLEEP_TIME = 2.0

    def __init__(self) -> None:
        """Initialize Scraper object and create scraper directory"""
        self.scrpdir = DUMP_PATH / "scraper"
        self.scrpdir.mkdir(exist_ok=True, parents=True)
        self.pvdir = self.scrpdir / "pvmag"
        self.pvdir.mkdir(exist_ok=True, parents=True)

    def _load_listing(self) -> None:
        fp = self.pvdir / "pvmag_usa.json"
        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.pvmag_articles = json.load(file)
            print(f"[*] {len(self.pvmag_articles):>05} articles loaded")
            self.first_time = False
        else:
            fp.touch()
            self.pvmag_articles = {}
            print(f"[*] {fp.name} does not exist, creating one.")
            self.first_time = True

    def _dump_listing(self) -> None:
        with open(self.pvdir / "pvmag_usa.json", "w") as f:
            json.dump(self.pvmag_articles, f, indent=4)
        print(f"[*] Dumped {len(self.pvmag_articles):>05} PVMag USA articles.")

    def _get_body(self, url: str) -> dict[str, Optional[str]]:
        sleep(PvMagUSAScraper.SLEEP_TIME)
        response = requests.get(
            url,
            proxies=PROXIES if USE_SOCKS is True else None,
            headers=PvMagUSAScraper.HEADERS,
        )
        if response.status_code != 200:
            print(
                f"[!] [{len(self.pvmag_articles):>05}] {response.status_code=}"
                f"No article body for {url}"
            )
            return {"body": None, "key_words": None}
        soup = BeautifulSoup(response.text, "html.parser")
        paras = soup.find("div", class_="entry-content").find_all("p")
        body = "\n".join(para.get_text() for para in paras[:-1])
        return {"body": re.sub(r"\s+", " ", body).strip(), "key_words": None}

    def fetch_body(self) -> None:
        self._load_listing()
        for ind, (k, v) in enumerate(self.pvmag_articles.items(), start=1):
            if v.get("body") is not None:
                print(
                    f"[*] [{ind:>05}/{len(self.pvmag_articles):>05}]"
                    f" Body for {k} already exist."
                )
                continue
            self.pvmag_articles[k] |= self._get_body(v["url"])
            print(
                f"[*] [{ind:>05}/{len(self.pvmag_articles):>05}]"
                f" fetched body for {k}"
            )
            if ind % 10 == 0:
                self._dump_listing()
        self._dump_listing()

    def _add_articles(self, response: requests.Response) -> bool:
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("div", class_="article-preview")
        if not articles:
            print("[?] No articles found, exiting")
            return False
        for article in articles:
            _h2 = article.find("h2", class_="entry-title")
            if _h2 is None:
                print("\t[?] No H2 tag found for title.")
                continue
            title = re.sub(r"\s+", " ", _h2.get_text(strip=True)).strip()
            url = _h2.find("a")["href"]
            _id = str(uuid5(NAMESPACE_DNS, title))
            if _id in self.pvmag_articles and self.first_time is False:
                print(f"\t[*] {repr(title)} already scraped.")
                print("\t[!] List is upto date, exiting.")
                return False
            date_published = article.find(
                "time",
                class_="entry-published updated",
            )["datetime"]
            author = article.find(
                "span",
                class_="entry-author",
            ).get_text(strip=True)
            try:
                summary = (
                    article.find("div", class_="article-lead-text")
                    .find("p")
                    .get_text(strip=True)
                )
                summary = re.sub(r"\s+", " ", summary).strip()
            except Exception:
                summary = None
            article_dict = {
                "article_id": _id,
                "url": url,
                "title": title,
                "date_published": re.sub(r"\s+", " ", date_published).strip(),
                "author": re.sub(r"\s+", " ", author).strip(),
                "summary": summary,
            }
            self.pvmag_articles[_id] = article_dict
            print(
                f"\t[*] [{len(self.pvmag_articles):>05}] "
                f"[{article_dict['date_published']}] "
                f"{article_dict['title']}"
            )
        return True

    def fetch_articles(self) -> None:
        self._load_listing()
        page_num = 1
        while True:
            requrl = f"https://www.pv-magazine-usa.com/news/page/{page_num}/"
            print(f"[*] Page Num = {page_num}")
            response = requests.get(
                url=requrl,
                headers=PvMagUSAScraper.HEADERS,
                proxies=PROXIES if USE_SOCKS is True else None,
            )
            if response.status_code == 404:
                print(
                    f"[!] [{len(self.pvmag_articles):>05}] "
                    f"{page_num=} {response.status_code=} "
                    "Reached EOL, exiting."
                )
                break
            if response.status_code != 200:
                print(
                    f"[!] [{len(self.pvmag_articles):>05}] "
                    f"{page_num=} {response.status_code=}"
                )
                continue
            if self._add_articles(response) is False:
                print("[?] Probably reached EOL, exiting.")
                break
            self._dump_listing()
            page_num += 1
        self._dump_listing()
