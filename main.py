from aggregate import DataTransformer
from ec import ECScraper
from eec import EECScraper
from nleec import NLEECScraper

print(" Economic Times ".center(50, "="))
ecscrap = ECScraper()
ecscrap.fetch_ec("hybrid")
ecscrap.fetch_ec("renewable-regulation")
ecscrap.fetch_ec("solar")

print(" Energy Economic Times ".center(50, "="))
eecscrap = EECScraper()
eecscrap.fetch_articles("all-news")
eecscrap.fetch_articles("renewable-news")
eecscrap.fetch_articles("economy-news")
eecscrap.fetch_articles("oil-news")
eecscrap.fetch_articles("coal-news")
eecscrap.fetch_articles("power-news")

print(" Energy Economic Times Newsletter ".center(50, "="))
nleescrapper = NLEECScraper()
nleescrapper.fetch_newsletters()
nleescrapper.fetch_articles()


json_files = {
    "ec": r"dump\scraper\ec\solar.json",
    "eec": r"dump\scraper\eec\renewable-news.json",
    "nleec": r"dump\scraper\nleec\renewable.json",
}
transformer = DataTransformer(json_files)
transformer.transform("./dump/scraper/articles.parquet")
