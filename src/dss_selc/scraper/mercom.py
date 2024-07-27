import json
from typing import Optional

import requests
from bs4 import BeautifulSoup

from dss_selc.utils import DUMP_PATH, PROXIES, USE_SOCKS


class MrcmScraper:
    GRAPHQL_ENDPOINT = "https://cms.mercomindia.com/graphql"
    GRAPHQL_QUERY = """
    query getPosts($offset: Int, $size: Int) {
        posts(where: {
            status: PUBLISH,
            categoryNotIn: [],
            offsetPagination: {offset: $offset, size: $size}
        }) {
            nodes {
                id
                slug
                date
                content
                title
                modifiedGmt
                categories {
                    nodes {
                        name
                        slug
                    }
                }
                featuredImage {
                    node {
                        mediaItemUrl
                    }
                }
                author {
                    node {
                        name
                        description
                        publicEmail
                        saboxSocialLinks {
                            twitter
                        }
                    }
                }
            }
        }
    }
    """
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0)",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://www.mercomindia.com/",
        "Content-Type": "application/json",
        "Origin": "https://www.mercomindia.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }
    MERCOM_BASE = "https://www.mercomindia.com/"

    def __init__(self) -> None:
        """Initialize Scraper object and create scraper directory"""
        self.scrpdir = DUMP_PATH / "scraper"
        self.scrpdir.mkdir(exist_ok=True, parents=True)
        self.mcmdir = self.scrpdir / "mercom"
        self.mcmdir.mkdir(exist_ok=True, parents=True)

    def _load_listing(self) -> None:
        fp = self.mcmdir / "mercom.json"
        if fp.exists():
            print(f"[*] {fp.name} exist, loading it.")
            with fp.open("r") as file:
                self.mcm_articles = json.load(file)
            print(f"[*] {len(self.mcm_articles):>05} articles loaded")
            # self.first_time = False

        else:
            fp.touch()
            self.mcm_articles = {}
            print(f"[*] {fp.name} does not exist, creating one.")
            # self.first_time = True

    def _dump_listing(self) -> None:
        with open(self.mcmdir / "mercom.json", "w") as f:
            json.dump(self.mcm_articles, f, indent=4)
        print(f"[*] Dumped {len(self.mcm_articles):>05} mercom articles.")

    def _add_articles(self, response: requests.Response) -> Optional[bool]:
        try:
            resp_json = response.json()
        except Exception as e:
            print(f"[!] [{len(self.mcm_articles):>05}] JSON Error! {str(e)}")
            return None

        articles = resp_json["data"]["posts"]["nodes"]
        if len(articles) == 0:
            return False

        for article in articles:
            article_id = article["id"]
            if article_id in self.mcm_articles:
                print(f"\t[*] {article_id} already scraped.")
                print("\t[!] List is upto date, exiting.")
                return False
            content = article["content"]
            if content is None:
                continue
            soup = BeautifulSoup(content, "html.parser")
            ab = " ".join(p.get_text(strip=True).strip() for p in soup.find_all("p"))
            article_info = {
                "title": article["title"],
                "url": MrcmScraper.MERCOM_BASE + article["slug"],
                "date": article["date"],
                "categories": [j["name"] for j in article["categories"]["nodes"]],
                "body": ab,
                "author": article["author"]["node"]["name"],
            }
            self.mcm_articles[article_id] = article_info
            print(
                f"\t[*] [{len(self.mcm_articles):>05}] "
                f"[{article['date']}] {article_info['title']}"
            )
        return True

    def fetch_articles(self) -> None:
        self._load_listing()
        offset = 0
        while True:
            print(f"[*] Offset = {offset}")
            variables = {"offset": offset, "size": 15}
            payload = {"query": MrcmScraper.GRAPHQL_QUERY, "variables": variables}

            response = requests.post(
                MrcmScraper.GRAPHQL_ENDPOINT,
                json=payload,
                headers=MrcmScraper.HEADERS,
                proxies=PROXIES if USE_SOCKS is True else None,
            )

            if response.status_code != 200:
                print(
                    f"[!] [{len(self.mcm_articles):>05}] "
                    f"{offset=} {response.status_code=}"
                )
            if self._add_articles(response) is False:
                print("[?] Probably reached EOL, exiting.")
                break
            self._dump_listing()
            offset += 15
        self._dump_listing()
