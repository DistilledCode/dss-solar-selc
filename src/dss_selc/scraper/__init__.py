import sys
import time
import traceback

from dss_selc.scraper.ec import ECScraper
from dss_selc.scraper.eec import EECScraper
from dss_selc.scraper.mercom import MrcmScraper
from dss_selc.scraper.nleec import NLEECScraper
from dss_selc.scraper.pvmag import PvMagScraper
from dss_selc.scraper.pvmag_global import PvMagGlobalScraper
from dss_selc.scraper.pvmag_usa import PvMagUSAScraper
from dss_selc.scraper.saur import SaurScraper


class Scraper:
    def __init__(self) -> None:
        self.ec = ECScraper()
        self.eec = EECScraper()
        self.nleec = NLEECScraper()
        self.mrcm = MrcmScraper()
        self.pvindia = PvMagScraper()
        self.pvglobal = PvMagGlobalScraper()
        self.pvusa = PvMagUSAScraper()
        self.saur = SaurScraper()

    def fetch_ec(self) -> None:
        print(" Economic Times ".center(50, "="))
        self.ec.fetch_ec("hybrid")
        self.ec.fetch_ec("renewable-regulation")
        self.ec.fetch_ec("solar")

    def fetch_eec(self) -> None:
        print(" Energy Economic Times ".center(50, "="))
        self.eec.fetch_articles("all-news")
        self.eec.fetch_articles("renewable-news")
        self.eec.fetch_articles("economy-news")
        self.eec.fetch_articles("oil-news")
        self.eec.fetch_articles("coal-news")
        self.eec.fetch_articles("power-news")

    def fetch_nleec(self) -> None:
        print(" Energy Economic Times Newsletter ".center(50, "="))
        self.nleec.fetch_newsletters()
        self.nleec.fetch_articles()

    def fetch_mercom(self) -> None:
        print(" Mercom ".center(50, "="))
        self.mrcm.fetch_articles()

    def fetch_pvinda(self) -> None:
        print(" PV Mag India ".center(50, "="))
        self.pvindia.fetch_articles()
        self.cautious_fetch(self.pvindia.fetch_body)

    def fetch_pvusa(self) -> None:
        print(" PV Mag USA ".center(50, "="))
        self.pvusa.fetch_articles()
        self.cautious_fetch(self.pvusa.fetch_body)

    def fetch_pvglobal(self) -> None:
        print(" PV Mag Global ".center(50, "="))
        self.pvglobal.fetch_articles()
        self.cautious_fetch(self.pvglobal.fetch_body)

    def fetch_saur(self) -> None:
        print(" Saur ".center(50, "="))
        self.cautious_fetch(self.saur.fetch_articles)
        self.cautious_fetch(self.saur.fetch_body)

    def fetch_all(self) -> None:
        self.fetch_ec()
        self.fetch_eec()
        self.fetch_nleec()
        self.fetch_mercom()
        self.fetch_pvinda()
        self.fetch_pvglobal()
        self.fetch_pvusa()
        self.fetch_saur()

    def cautious_fetch(self, method: callable, ts: int = 2) -> None:
        try:
            method()
        except Exception as e:
            ts += 2
            print(f"Sleeping for {min(300, ts)}s\n{str(e)=}")
            exc_type, _, exc_tb = sys.exc_info()
            fname = traceback.extract_tb(exc_tb)[-1][0]
            line_number = traceback.extract_tb(exc_tb)[-1][1]
            print(f"Exception type: {exc_type}")
            print(f"File name: {fname}:{line_number}")
            print(f"Error message: {str(e)}")

            time.sleep(min(300, ts))
            self.cautious_fetch(method, ts)
