from dss_selc.data_transform.transform import transform_data
from dss_selc.scraper import Scraper

scraper = Scraper()
scraper.fetch_all()

transform_data()
