"""Download CHAP annual PM2.5 (Y1K V4) from Zenodo."""
from __future__ import annotations

import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "chap_y1k"
RAW.mkdir(parents=True, exist_ok=True)

YEARS = list(range(2010, 2020))
RECORD = "6398971"

for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})


def file_url(year: int) -> str:
    meta = SESSION.get(f"https://zenodo.org/api/records/{RECORD}", timeout=60)
    meta.raise_for_status()
    key = f"CHAP_PM2.5_Y1K_{year}_V4.nc"
    for item in meta.json()["files"]:
        if item["key"] == key:
            return item["links"]["self"]
    raise KeyError(key)


def download(year: int) -> None:
    dest = RAW / f"CHAP_PM2.5_Y1K_{year}_V4.nc"
    alt = ROOT.parent / "Air-Exploratory" / "data" / "raw" / "chap_y1k" / dest.name
    if alt.exists() and not dest.exists():
        dest.write_bytes(alt.read_bytes())
        print(f"copy {dest.name} from Air-Exploratory")
        return
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"skip {dest.name}")
        return
    url = file_url(year)
    print(f"download {dest.name} ...")
    resp = SESSION.get(url, timeout=300)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"  saved {dest.stat().st_size // 1024 // 1024} MB")


if __name__ == "__main__":
    for year in YEARS:
        download(year)
