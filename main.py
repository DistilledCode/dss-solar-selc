from ec import ECScrapper
from eec import EECScrapper

ecscrapper = ECScrapper()
ecscrapper.fetch_ec("hybrid")
ecscrapper.fetch_ec("renewable-regulation")
ecscrapper.fetch_ec("solar")

eecscrapper = EECScrapper()
eecscrapper.fetch_articles("all-news")
eecscrapper.fetch_articles("renewable-news")
eecscrapper.fetch_articles("economy-news")
eecscrapper.fetch_articles("oil-news")
eecscrapper.fetch_articles("coal-news")
eecscrapper.fetch_articles("power-news")
