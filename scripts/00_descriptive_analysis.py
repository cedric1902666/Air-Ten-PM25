"""Descriptive statistics and trend figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "panel.csv"
TAB = ROOT / "tables"
FIG = ROOT / "figures"

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

VARS = [
    ("pm25", "PM2.5（µg/m³）"),
    ("ln_pm25", "ln(PM2.5)"),
    ("ln_gdp_pc", "ln(人均GDP)"),
    ("secondary_pct", "第二产业比重(%)"),
    ("tertiary_pct", "第三产业比重(%)"),
]


def main() -> None:
    TAB.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)
    df = pd.read_csv(DATA)

    rows = []
    for col, label in VARS:
        s = df[col].dropna()
        rows.append({
            "variable": label,
            "n": len(s),
            "mean": s.mean(),
            "std": s.std(),
            "min": s.min(),
            "p50": s.median(),
            "max": s.max(),
        })
    desc = pd.DataFrame(rows)
    desc.to_csv(TAB / "descriptive_stats.csv", index=False, encoding="utf-8-sig")

    trend = (
        df.groupby(["year", "treat"], as_index=False)["pm25"]
        .mean()
        .rename(columns={"pm25": "mean_pm25"})
    )
    trend["group"] = trend["treat"].map({0: "对照组", 1: "重点区域"})
    trend.to_csv(TAB / "pm25_trend_by_group.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(8, 5))
    for grp, sub in trend.groupby("group"):
        ax.plot(sub["year"], sub["mean_pm25"], marker="o", label=grp)
    ax.axvline(2013.5, color="gray", linestyle="--", lw=1)
    ax.set_xlabel("年份")
    ax.set_ylabel("PM2.5 年均浓度 (ug/m3)")
    ax.set_title("重点区域与对照组 PM2.5 均值趋势（CHAP Y1K）")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig1_pm25_trend.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    yearly = df.groupby("year").agg(
        n_city=("city_key", "nunique"),
        mean_pm25=("pm25", "mean"),
        treat_mean=("pm25", lambda x: df.loc[x.index[df.loc[x.index, "treat"] == 1], "pm25"].mean()),
    )
    yearly.to_csv(TAB / "yearly_summary.csv", encoding="utf-8-sig")
    print(desc.to_string(index=False))
    print(f"Saved {TAB / 'descriptive_stats.csv'} and {FIG / 'fig1_pm25_trend.png'}")


if __name__ == "__main__":
    main()
