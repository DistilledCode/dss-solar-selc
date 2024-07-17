from aggregate import DataTransformer

json_files = {
    "ec": r"dump/scraper/ec/solar.json",
    "eec": r"dump/scraper/eec/renewable-news.json",
    "nleec": r"dump/scraper/nleec/renewable.json",
}
transformer = DataTransformer(json_files)
transformer.transform("./dump/scraper/articles.parquet")
