import time

from ec import ECScraper
from eec import EECScraper
from mercom import MrcmScraper
from nleec import NLEECScraper
from pvmag import PvMagScraper
from saur import SaurScraper

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


print(" Mercom ".center(30, "="))
mrcmscraper = MrcmScraper()
mrcmscraper.fetch_articles()


print(" Saur ".center(30, "="))
saurscraper = SaurScraper()


def get_saur_body(ts: int = 60) -> None:
    try:
        saurscraper.fetch_body()
    except Exception:
        ts += 2
        print(f"Sleeping for {min(300, ts)}s")
        time.sleep(min(300, ts))
        get_saur_body(ts)


saurscraper.fetch_articles()
get_saur_body()


print(" PV Mag ".center(30, "="))
pvscraper = PvMagScraper()
pvscraper.fetch_articles()
pvscraper.fetch_body()
