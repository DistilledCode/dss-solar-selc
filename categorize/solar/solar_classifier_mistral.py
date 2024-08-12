import json
import warnings
from pathlib import Path
from typing import Any

import pandas as pd
import requests

warnings.filterwarnings("ignore", category=UserWarning)

PROMPT = """
You are a specialized Text Classification AI designed for solar energy content analysis.
Your task is to evaluate input text and provide probability scores for two categories:
    - solar
    - notSolar

Task:
1. Analyze the given text input.
2. Assign probability scores (0.00 to 1.00) for each category.
3. Provide only the probability scores without additional explanation.

Category Definitions:
solar: Content primarily focused on solar energy, including but not limited to:
- Solar power technologies
- Photovoltaic systems
- Solar panels
- Solar thermal applications
- Solar industry news
- Solar energy policies and regulations

notSolar: Content not primarily concerned with solar energy or solar-related topics.

The output should strictly follow the provided JSON schema:
{frmt}

Here is the text that needs classification

Text:
'''
{text}
'''
"""


JSON_FRMT = """
{
    "solar": "number",
    "notSolar": "number"
}
"""

SYS_PROMPT = "<s>[INST]{prompt}[/INST]"

dp = Path("../dss-selc-dump/solar_category/")
dp.mkdir(parents=True, exist_ok=True)

fp = dp / "articles_s_mistral.parquet"

if fp.exists():
    df_path = fp
    print("df exist, will start from it.")
else:
    df_path = "../dss-selc-dump/scraper/articles.parquet"
    print("df doesn't exist, starting from scratch.")


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
        "http://10.100.87.69:8080/completion",
        data=json.dumps(payload),
    )
    return response.json()["content"]


df = pd.read_parquet(df_path)
if not fp.exists():
    df["solar_p"] = 999.0
    df["not_solar_p"] = 999.0
for ind in range(len(df)):
    if df.iloc[ind, -1] != 999.0:
        print(f"[{ind:>05}/{len(df):>05}] Already categorized")
        continue
    title = df.iloc[ind, 1]
    response = json.loads(get_resp(title))
    print(f"[{ind:>05}/{len(df):>05}] {title}")
    print(
        f"[{ind:>05}/{len(df):>05}] solar: {float(response['solar'])}; "
        f"not solar: {float(response['notSolar'])}"
    )
    df.iloc[ind, -1] = float(response["notSolar"])
    df.iloc[ind, -2] = float(response["solar"])
    if ind % 10 == 0:
        df.to_parquet(fp)
df.to_parquet(fp)
