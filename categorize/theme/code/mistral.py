import json
import warnings
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from dss_selc.utils import PRJ_PATH

warnings.filterwarnings("ignore", category=UserWarning)


JSON_FRMT = """
{
    "pr": "number",
    "mi": "number",
    "ti": "number",
    "pa": "number",
    "fi": "number"
}
"""


def get_df_path(fname: Path | str) -> Path:
    solar_predicted = (
        "dss-selc-dump/",
        "classification/",
        "solar_category/",
        "solar_predicted_bayesian.parquet",
    )
    target_path = Path(PRJ_PATH / "dss-selc-dump/classification/solar_theme/")
    target_path.mkdir(parents=True, exist_ok=True)

    file_path = target_path / fname
    if file_path.exists():
        df_path = file_path
        print("df exist, will start from it.")
    else:
        df_path = PRJ_PATH / "".join(solar_predicted)
        print("df doesn't exist, starting from scratch.")
    return file_path, df_path


def get_resp(title: str) -> dict[str, Any]:
    prompt = PROMPT.format(frmt=JSON_FRMT, text=title)
    sys_prompt = SYS_PROMPT.format(prompt=prompt)
    payload = {
        "prompt": sys_prompt,
        "dynatemp_range": 0.00,
        "cache_prompt": True,
        "temperature": 0.5,
    }
    response = requests.post(
        f"http://localhost:{PORT}/completion",
        data=json.dumps(payload),
    )
    return response.json()["content"]


with open(PRJ_PATH / "categorize/theme/theme_prompt.txt", "r") as f:
    PROMPT = " ".join(f.readlines())

PORT = 8080
FNAME = "theme_train_m.parquet"
SYS_PROMPT = "<s>[INST]{prompt}[/INST]"

SOLAR_THRESHOLD = 0.69
grammar_file = PRJ_PATH / "categorize/theme/grammar/theme_grammar.gbnf"


response = requests.get(f"http://localhost:{PORT}/health")
print(f"Server response status: {response.status_code}")
assert response.status_code == 200
fp, df_path = get_df_path(FNAME)
df = pd.read_parquet(df_path)
if not fp.exists():
    for i in ("pr", "mi", "ti", "pa", "fi"):
        df[i] = 999.0
for ind in range(len(df)):

    if df.iloc[ind, -1] != 999.0:
        print(f"[{ind:>05}/{len(df):>05}] Already categorized")
        continue

    if df.iloc[ind, -6] < SOLAR_THRESHOLD:
        print(f"[{ind:>05}/{len(df):>05}] Not solar-related")
        continue

    title = df.iloc[ind, 1]
    response = json.loads(get_resp(title))
    print(f"[{ind:>05}/{len(df):>05}] {title}")
    print(
        f"[{ind:>05}/{len(df):>05}] "
        f"pr: {float(response['pr'])} "
        f"mi: {float(response['mi'])} "
        f"ti: {float(response['ti'])} "
        f"pa: {float(response['pa'])} "
        f"fi: {float(response['fi'])}"
    )
    df.iloc[ind, -1] = float(response["fi"])
    df.iloc[ind, -2] = float(response["pa"])
    df.iloc[ind, -3] = float(response["ti"])
    df.iloc[ind, -4] = float(response["mi"])
    df.iloc[ind, -5] = float(response["pr"])
    if ind % 10 == 0:
        print(f"[{ind:>05}/{len(df):>05}] Dumping DF")
        df.to_parquet(fp)
    if ind > 5000:
        print("Reached End, exiting!")
        break
df.to_parquet(fp)
exit(0)
