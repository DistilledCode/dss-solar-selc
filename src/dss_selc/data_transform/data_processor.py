import json
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from dateutil import parser


class DataProcessor:
    def __init__(self, json_files: dict[str, str]) -> None:
        self.json_files = json_files
        self.json_data = {}
        self.data = []
        self.df = None

    @staticmethod
    def load_json(file_path: str) -> list | dict:
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def ensure_list(value: Optional[list | str]) -> list:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [value]
        if pd.isna(value):
            return []
        return [str(value)]

    @staticmethod
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
                "title": v.get("headline"),
                "summary": v.get("description"),
                "body": v.get("articleBody"),
                "date": v.get("datePublished"),
                "kws": DataProcessor.ensure_list(v.get("keywords")),
                "source": source,
            }

            return article
        except Exception as e:
            print(f"Error processing article {k}: {str(e)}")
            return None

    @staticmethod
    def parse_date(date_string: str) -> datetime:
        return parser.parse(date_string)

    def load_json_data(self) -> None:
        self.json_data = {k: self.load_json(v) for k, v in self.json_files.items()}

    def process_articles(self) -> None:
        for source, articles in self.json_data.items():
            for k, v in articles.items():
                article = self.process_article(k, v, source)
                if article is not None:
                    self.data.append(article)

    def create_dataframe(self) -> None:
        self.df = pd.DataFrame(self.data)
        self.df["kws"] = self.df["kws"].apply(self.ensure_list)

        def parse_date(date_str: str) -> Optional[datetime.date]:
            try:
                return parser.parse(date_str).date()
            except Exception:
                return None

        self.df["date"] = self.df["date"].apply(parse_date)
        self.df["date"] = pd.to_datetime(self.df["date"])

    def process_additional_sources(self, src_dict: dict[str, str]) -> None:
        # Process Mercom data
        with open(src_dict["mercom"], "r") as f:
            mercom = pd.read_json(f).transpose().reset_index(drop=True)

        mercom = mercom[["url", "title", "body", "date", "categories"]]
        mercom.columns = ["url", "title", "body", "date", "kws"]
        mercom["source"] = "mercom"
        mercom["date"] = pd.to_datetime(mercom["date"]).dt.date

        # Process Saur data
        with open(src_dict["saur"], "r") as f:
            saur = pd.read_json(f).transpose().reset_index(drop=True)

        saur = saur[["url", "title", "summary", "body", "date_published", "key_words"]]
        saur.columns = ["url", "title", "summary", "body", "date", "kws"]
        saur["source"] = "saur"
        saur["date"] = saur["date"].str.replace(
            r"(\d+)(st|nd|rd|th)", r"\1", regex=True
        )
        saur["date"] = pd.to_datetime(saur["date"], format="%a, %b %d, %Y").dt.date

        # Process PV Magazine data
        with open(src_dict["pvmag"], "r") as f:
            pvmag = pd.read_json(f).transpose().reset_index(drop=True)

        pvmag = pvmag[
            [
                "url",
                "title",
                "summary",
                "body",
                "date_published",
                "key_words",
            ]
        ]
        pvmag.columns = ["url", "title", "summary", "body", "date", "kws"]
        pvmag["source"] = "pvmag"
        pvmag["date"] = pd.to_datetime(pvmag["date"]).dt.date

        with open(src_dict["pvmag_global"], "r") as f:
            pvmag_gl = pd.read_json(f).transpose().reset_index(drop=True)

        pvmag_gl = pvmag_gl[
            [
                "url",
                "title",
                "summary",
                "body",
                "date_published",
                "key_words",
            ]
        ]
        pvmag_gl.columns = ["url", "title", "summary", "body", "date", "kws"]
        pvmag_gl["source"] = "pvmag_global"
        pvmag_gl["date"] = pd.to_datetime(pvmag_gl["date"], utc=True).dt.date

        with open(src_dict["pvmag_us"], "r") as f:
            pvmag_us = pd.read_json(f).transpose().reset_index(drop=True)

        pvmag_us = pvmag_us[
            [
                "url",
                "title",
                "summary",
                "body",
                "date_published",
                "key_words",
            ]
        ]
        pvmag_us.columns = ["url", "title", "summary", "body", "date", "kws"]
        pvmag_us["source"] = "pvmag_us"
        pvmag_us["date"] = pd.to_datetime(pvmag_us["date"], utc=True).dt.date

        # Combine all dataframes
        self.df = pd.concat(
            [self.df, mercom, saur, pvmag, pvmag_gl, pvmag_us], axis=0
        ).reset_index(drop=True)

        # Ensure all dates in the combined DataFrame are date objects
        self.df["date"] = pd.to_datetime(self.df["date"])

    def save_to_parquet(self, output_path: str) -> None:
        self.df.to_parquet(output_path)

    def transform(self, src_dict: dict[str, str], output_path: str) -> None:
        self.load_json_data()
        self.process_articles()
        self.create_dataframe()
        self.process_additional_sources(src_dict)
        self.save_to_parquet(output_path)

        print(f"Processed {len(self.df)} articles")
