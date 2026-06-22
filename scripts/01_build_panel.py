"""Build city-year panel: CHAP PM2.5 + APPCAP treatment + CityEdu controls."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "chap_y1k"
REGIONS = ROOT / "data" / "appcap_regions.csv"
GEO = ROOT.parent / "CityEdu-Eco" / "data" / "china_cities.geojson"
CITYEDU = ROOT.parent / "CityEdu-Eco" / "data" / "panel.csv"
OUT = ROOT / "data" / "panel.csv"
YEARS = list(range(2010, 2020))


def normalize_name(name: str) -> str:
    for suffix in ("市", "地区", "盟", "州", "省"):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


def load_city_coords() -> pd.DataFrame:
    with GEO.open(encoding="utf-8") as f:
        geo = json.load(f)
    rows = []
    for feat in geo["features"]:
        props = feat["properties"]
        if props.get("level") not in ("city", "province"):
            continue
        lon, lat = props.get("centroid") or props.get("center")
        rows.append(
            {
                "city_key": normalize_name(props["name"]),
                "geo_name": props["name"],
                "province": normalize_name(props.get("province", props["name"])),
                "lon": lon,
                "lat": lat,
                "level": props["level"],
            }
        )
    df = pd.DataFrame(rows)
    return df.sort_values(["city_key", "level"]).drop_duplicates("city_key", keep="first")


def load_treatment_rules() -> tuple[set[str], set[str]]:
    rules = pd.read_csv(REGIONS)
    prov_treat: set[str] = set()
    city_treat: set[str] = set()
    for _, row in rules.iterrows():
        members = [m.strip() for m in str(row["members"]).split("|")]
        if row["scope"] == "province":
            prov_treat.update(members)
        else:
            city_treat.update(members)
    return prov_treat, city_treat


def assign_treat(cities: pd.DataFrame) -> pd.DataFrame:
    prov_treat, city_treat = load_treatment_rules()
    cities = cities.copy()
    cities["treat"] = (
        cities["province"].isin(prov_treat) | cities["city_key"].isin(city_treat)
    ).astype(int)
    cities["post"] = 0
    cities["treat_post"] = 0
    return cities


def sample_year(year: int, cities: pd.DataFrame) -> pd.DataFrame:
    path = RAW / f"CHAP_PM2.5_Y1K_{year}_V4.nc"
    if not path.exists():
        raise FileNotFoundError(path)
    ds = xr.open_dataset(path)
    var = "PM2.5" if "PM2.5" in ds else list(ds.data_vars)[0]
    da = ds[var]
    lats = da["lat"].values if "lat" in da.coords else da.coords[list(da.dims)[-2]].values
    lons = da["lon"].values if "lon" in da.coords else da.coords[list(da.dims)[-1]].values
    vals = []
    for _, row in cities.iterrows():
        j = int(np.abs(lats - row["lat"]).argmin())
        i = int(np.abs(lons - row["lon"]).argmin())
        vals.append(float(da.values[j, i]))
    ds.close()
    out = cities.copy()
    out["year"] = year
    out["pm25"] = vals
    return out


def add_econ_controls(panel: pd.DataFrame) -> pd.DataFrame:
    econ = pd.read_csv(CITYEDU)
    econ = econ[econ["year"].between(min(YEARS), max(YEARS))]
    merged = panel.merge(econ, on=["city_key", "year"], how="left")
    merged["gdp_pc"] = merged["gdp"] / merged["population"].replace(0, np.nan)
    merged["ln_pm25"] = np.log(merged["pm25"].clip(lower=1.0))
    merged["ln_gdp_pc"] = np.log(merged["gdp_pc"].clip(lower=0.1))
    merged["ln_fiscal"] = np.log(merged["fiscal_revenue"].clip(lower=0.1))
    merged["ln_pop"] = np.log(merged["population"].clip(lower=0.1))
    merged["post"] = (merged["year"] >= 2014).astype(int)
    merged["treat_post"] = merged["treat"] * merged["post"]
    merged["rel_year"] = merged["year"] - 2014
    return merged


def main() -> None:
    cities = assign_treat(load_city_coords())
    parts = [sample_year(y, cities) for y in YEARS]
    pm = pd.concat(parts, ignore_index=True)
    panel = add_econ_controls(pm)
    panel = panel.dropna(subset=["pm25"])
    panel.to_csv(OUT, index=False, encoding="utf-8-sig")
    n_city = panel.city_key.nunique()
    n_treat = panel.loc[panel.treat == 1, "city_key"].nunique()
    print(f"wrote {OUT}: {len(panel)} rows, {n_city} cities ({n_treat} treated)")


if __name__ == "__main__":
    main()
