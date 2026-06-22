"""Baseline TWFE DiD: APPCAP × PM2.5."""
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

CONTROLS = "ln_gdp_pc + secondary_pct + tertiary_pct + ln_fiscal"


def fit_model(df: pd.DataFrame, label: str, controls: str | None = CONTROLS) -> pd.DataFrame:
    sub = df.dropna(subset=["ln_pm25", "treat_post"])
    if controls:
        sub = sub.dropna(subset=["ln_gdp_pc", "secondary_pct", "tertiary_pct", "ln_fiscal"])
    ctrl_part = f" + {controls}" if controls else ""
    formula = f"ln_pm25 ~ treat_post{ctrl_part} + C(city_key) + C(year)"
    model = smf.ols(formula, data=sub).fit(
        cov_type="cluster",
        cov_kwds={"groups": sub["city_key"].astype(str)},
    )
    row = {
        "model": label,
        "coef_treat_post": model.params.get("treat_post", np.nan),
        "se": model.bse.get("treat_post", np.nan),
        "p_value": model.pvalues.get("treat_post", np.nan),
        "ci_low": model.conf_int().loc["treat_post", 0] if "treat_post" in model.params else np.nan,
        "ci_high": model.conf_int().loc["treat_post", 1] if "treat_post" in model.params else np.nan,
        "r_squared": model.rsquared,
        "n_obs": int(model.nobs),
        "n_city": sub.city_key.nunique(),
    }
    with open(TAB / f"did_{label}_summary.txt", "w", encoding="utf-8") as f:
        f.write(model.summary().as_text())
    return pd.DataFrame([row])


def main() -> None:
    TAB.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    df = pd.read_csv(DATA)

    results = pd.concat([
        fit_model(df, "with_controls"),
        fit_model(df, "gdp_only", controls="ln_gdp_pc"),
        fit_model(df, "no_controls", controls=None),
    ], ignore_index=True)
    results.to_csv(TAB / "did_results.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ypos = np.arange(len(results))
    ax.errorbar(
        results["coef_treat_post"], ypos,
        xerr=1.96 * results["se"], fmt="o", color="steelblue", capsize=4,
    )
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels(results["model"])
    ax.set_xlabel("treat × post 系数（95% CI，ln PM2.5）")
    ax.set_title("大气十条对 PM2.5 的双重差分估计")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_did_coef.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
