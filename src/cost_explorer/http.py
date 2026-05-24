from __future__ import annotations

from io import StringIO

import pandas as pd
import requests


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; llm-cost-explorer/0.1; +https://github.com/)",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_html(url: str, timeout: int = 45) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def read_html_tables(html: str) -> list[pd.DataFrame]:
    return pd.read_html(StringIO(html))
