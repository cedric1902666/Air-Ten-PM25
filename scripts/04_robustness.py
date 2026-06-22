"""Robustness checks for APPCAP DiD."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "panel.csv"
TAB = ROOT / "tables"

CONTROLS = "ln_gdp_pc + secondary_pct + tertiary_pct + ln_fiscal"


def run_did(df: pd.DataFrame, label: str) -> dict:
    sub = df.dropna(subset=["ln_pm25", "treat_post", "ln_gdp_pc", "secondary_pct", "tertiary_pct", "ln_fiscal"])
    formula = f"ln_pm25 ~ treat_post + {CONTROLS} + C(city_key) + C(year)"
    m = smf.ols(formula, data=sub).fit(
        cov_type="cluster",
        cov_kwds={"groups": sub["city_key"].astype(str)},
    )
    return {
        "spec": label,
        "coef": m.params.get("treat_post", np.nan),
        "se": m.bse.get("treat_post", np.nan),
        "p_value": m.pvalues.get("treat_post", np.nan),
        "n_obs": int(m.nobs),
        "n_city": sub.city_key.nunique(),
    }


def main() -> None:
    TAB.mkdir(exist_ok=True)
    df = pd.read_csv(DATA)

    specs = []

    # 1. Baseline
    specs.append(run_did(df, "baseline"))

    # 2. Exclude 2013 (pre-policy spike)
    d2 = df[df["year"] != 2013].copy()
    specs.append(run_did(d2, "drop_2013"))

    # 3. Post from 2015
    d3 = df.copy()
    d3["treat_post"] = d3["treat"] * (d3["year"] >= 2015).astype(int)
    specs.append(run_did(d3, "post_from_2015"))

    # 4. JJJ + YRD only (exclude PRD cities from treat)
    prd = {"广州", "深圳", "珠海", "佛山", "惠州", "东莞", "中山", "江门", "肇庆"}
    d4 = df.copy()
    d4.loc[d4["city_key"].isin(prd), "treat"] = 0
    d4["treat_post"] = d4["treat"] * d4["post"]
    specs.append(run_did(d4, "jjj_yrd_only"))

    # 5. Level PM2.5 instead of log
    sub = df.dropna(subset=["pm25", "treat_post", "ln_gdp_pc", "secondary_pct", "tertiary_pct", "ln_fiscal"])
    m5 = smf.ols(
        f"pm25 ~ treat_post + {CONTROLS} + C(city_key) + C(year)", data=sub
    ).fit(cov_type="cluster", cov_kwds={"groups": sub["city_key"].astype(str)})
    specs.append({
        "spec": "level_pm25",
        "coef": m5.params.get("treat_post", np.nan),
        "se": m5.bse.get("treat_post", np.nan),
        "p_value": m5.pvalues.get("treat_post", np.nan),
        "n_obs": int(m5.nobs),
        "n_city": sub.city_key.nunique(),
    })

    out = pd.DataFrame(specs)
    out.to_csv(TAB / "robustness_results.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
