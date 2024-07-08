from ec import ECScraper
from eec import EECScraper

ecscrap = ECScraper()
ecscrap.fetch_ec("hybrid")
ecscrap.fetch_ec("renewable-regulation")
ecscrap.fetch_ec("solar")

eecscrap = EECScraper()
eecscrap.fetch_articles("all-news")
eecscrap.fetch_articles("renewable-news")
eecscrap.fetch_articles("economy-news")
eecscrap.fetch_articles("oil-news")
eecscrap.fetch_articles("coal-news")
eecscrap.fetch_articles("power-news")
