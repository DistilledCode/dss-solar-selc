import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from dateutil import parser


def load_json(file_path: str) -> list | dict:
    with open(file_path, "r") as f:
        return json.load(f)


def ensure_list(value: Optional[list | str]) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    if pd.isna(value):
        return []
    return [str(value)]


def process_article(
    k: str,
    v: dict[str, Any],
    source: str,
) -> Optional[dict[str, Any]]:
    try:
        if source in ["eec", "nleec"]:
            v = v.get("data", {})
            if not v or (source == "nleec" and "articleBody" not in v):
                return None

        article = {
            "url": v.get("url"),
            "date_published": v.get("datePublished"),
            "section": v.get("articleSection"),
            "headline": v.get("headline"),
            "summary": v.get("description"),
            "body": v.get("articleBody"),
            "publisher_type": v.get("publisher", {}).get("@type"),
            "publisher_name": v.get("publisher", {}).get("name"),
            "key_words": ensure_list(v.get("keywords")),  # Use ensure_list here
        }

        author = v.get("author", {})
        if isinstance(author, list):
            author = author[0]
        article["author_type"] = author.get("@type")
        article["author_name"] = author.get("name")

        return article
    except Exception as e:
        print(f"Error processing article {k}: {str(e)}")
        return None


def parse_date(date_string: str) -> datetime:
    # try:
    #     return parser.parse(date_string)
    # except Exception:
    #     return pd.NaT
    return parser.parse(date_string)


json_files = {
    "ec": r"dump\scraper\ec\solar.json",
    "eec": r"dump\scraper\eec\renewable-news.json",
    "nleec": r"dump\scraper\nleec\renewable.json",
}

with ThreadPoolExecutor() as executor:
    json_data = {k: executor.submit(load_json, v) for k, v in json_files.items()}
    json_data = {k: v.result() for k, v in json_data.items()}

print(*[len(v) for v in json_data.values()], sum(len(v) for v in json_data.values()))

with ThreadPoolExecutor() as executor:
    data = []
    for source, articles in json_data.items():
        data.extend(
            executor.map(
                lambda item: process_article(*item, source),
                articles.items(),
            )
        )

data = [article for article in data if article is not None]

df = pd.DataFrame(data)

df["key_words"] = df["key_words"].apply(ensure_list)

df["date_published"] = df["date_published"].apply(parse_date)

df.to_parquet("./dump/scraper/articles.parquet")

print(f"Processed {len(df)} articles")
