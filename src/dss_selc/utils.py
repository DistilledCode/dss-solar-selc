from pathlib import Path

USE_SOCKS = True
SOCKS_PROXY = "socks5://127.0.0.1:1080"
PROXIES = {"http": SOCKS_PROXY, "https": SOCKS_PROXY}
SRC_PATH = Path(__file__).parent.parent.parent
DUMP_PATH = SRC_PATH / "dss-selc-dump"
