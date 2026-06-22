"""Event study relative to 2014 (first full implementation year)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "panel.csv"
TAB = ROOT / "tables"
FIG = ROOT / "figures"

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

K_MIN, K_MAX, K_OMIT = -4, 5, -1
CONTROLS = "ln_gdp_pc + secondary_pct + tertiary_pct + ln_fiscal"


def rel_col(k: int) -> str:
    return f"rel_m{abs(k)}" if k < 0 else f"rel_p{k}"


def add_event_dummies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for k in range(K_MIN, K_MAX + 1):
        if k == K_OMIT:
            continue
        out[rel_col(k)] = ((out["treat"] == 1) & (out["rel_year"] == k)).astype(int)
    return out


def main() -> None:
    TAB.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    df = add_event_dummies(pd.read_csv(DATA))
    sub = df.dropna(subset=["ln_pm25", "ln_gdp_pc", "secondary_pct", "tertiary_pct", "ln_fiscal"])

    evt_cols = [rel_col(k) for k in range(K_MIN, K_MAX + 1) if k != K_OMIT]
    evt_cols = [c for c in evt_cols if sub[c].nunique() > 1]
    formula = "ln_pm25 ~ " + " + ".join(evt_cols) + f" + {CONTROLS} + C(city_key) + C(year)"
    model = smf.ols(formula, data=sub).fit(
        cov_type="cluster",
        cov_kwds={"groups": sub["city_key"].astype(str)},
    )

    rows = []
    for k in range(K_MIN, K_MAX + 1):
        if k == K_OMIT:
            rows.append({"rel_year": k, "coef": 0.0, "se": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_value": np.nan})
            continue
        name = rel_col(k)
        if name not in model.params:
            continue
        rows.append({
            "rel_year": k,
            "coef": model.params[name],
            "se": model.bse[name],
            "ci_low": model.conf_int().loc[name, 0],
            "ci_high": model.conf_int().loc[name, 1],
            "p_value": model.pvalues[name],
        })
    es = pd.DataFrame(rows).sort_values("rel_year")
    es.to_csv(TAB / "event_study_coef.csv", index=False, encoding="utf-8-sig")
    with open(TAB / "event_study_summary.txt", "w", encoding="utf-8") as f:
        f.write(model.summary().as_text())

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.errorbar(
        es["rel_year"], es["coef"],
        yerr=1.96 * es["se"], fmt="o-", color="darkred", ecolor="gray", capsize=4,
    )
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(-0.5, color="gray", linestyle="--", lw=1)
    ax.set_xlabel("相对 2014 年的期数")
    ax.set_ylabel("Treat × 相对期（ln PM2.5）")
    ax.set_title("大气十条动态效应：事件研究")
    fig.tight_layout()
    fig.savefig(FIG / "fig3_event_study.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(es.to_string(index=False))


if __name__ == "__main__":
    main()
