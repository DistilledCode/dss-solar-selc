from dss_selc.data_transform.data_processor import DataProcessor
from dss_selc.utils import DUMP_PATH

json_files = {
    "ec": DUMP_PATH / "scraper/ec/solar.json",
    "eec": DUMP_PATH / "scraper/eec/renewable-news.json",
    "nleec": DUMP_PATH / "scraper/nleec/renewable.json",
}


def transform_data() -> None:
    transformer = DataProcessor(json_files)

    other_sources = {
        "mercom": DUMP_PATH / "scraper/mercom/mercom.json",
        "saur": DUMP_PATH / "scraper/saur/saur.json",
        "pvmag": DUMP_PATH / "scraper/pvmag/pvmag.json",
        "pvmag_global": DUMP_PATH / "scraper/pvmag/pvmag_global.json",
        "pvmag_us": DUMP_PATH / "scraper/pvmag/pvmag_usa.json",
    }
    transformer.transform(other_sources, DUMP_PATH / "scraper/articles.parquet")
