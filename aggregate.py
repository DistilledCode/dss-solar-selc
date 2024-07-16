import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from dateutil import parser


class DataTransformer:
    def __init__(self, json_files: dict[str, str]) -> None:
        self.json_files = json_files
        self.json_data = {}
        self.data = []
        self.df = None

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
                "key_words": DataTransformer.ensure_list(v.get("keywords")),
            }

            author = v.get("author", {})
            if isinstance(author, list):
                author = author[0]
            article["author_type"] = author.get("@type")
            article["author_name"] = author.get("name")
            article["source"] = source

            return article
        except Exception as e:
            print(f"Error processing article {k}: {str(e)}")
            return None

    def parse_date(date_string: str) -> datetime:
        return parser.parse(date_string)

    def load_json_data(self) -> None:
        with ThreadPoolExecutor() as executor:
            self.json_data = {
                k: executor.submit(self.load_json, v)
                for k, v in self.json_files.items()
            }
            self.json_data = {k: v.result() for k, v in self.json_data.items()}

    def process_articles(self) -> None:
        with ThreadPoolExecutor() as executor:
            for source, articles in self.json_data.items():
                self.data.extend(
                    executor.map(
                        lambda item: self.process_article(*item, source),
                        articles.items(),
                    )
                )

        self.data = [article for article in self.data if article is not None]

    def create_dataframe(self) -> None:
        self.df = pd.DataFrame(self.data)
        self.df["key_words"] = self.df["key_words"].apply(self.ensure_list)
        self.df["date_published"] = self.df["date_published"].apply(self.parse_date)

    def save_to_parquet(self, output_path: str) -> None:
        self.df.to_parquet(output_path)

    def transform(self, output_path: str) -> None:
        self.load_json_data()
        print(
            *[len(v) for v in self.json_data.values()],
            sum(len(v) for v in self.json_data.values()),
        )

        self.process_articles()
        self.create_dataframe()
        self.save_to_parquet(output_path)

        print(f"Processed {len(self.df)} articles")
