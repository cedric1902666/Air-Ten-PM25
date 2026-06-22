# Air-Ten-PM25

**《大气污染防治行动计划》是否降低了城市 PM2.5？——城市面板双重差分的证据**

复旦大学《社会科学数据挖掘》期末 Comprehensive Paper 项目。

**作者：** 蔡长霄（23307110294）  
**论文 PDF：** `paper/蔡长霄_23307110294_Air-Ten-PM25.pdf`

## 方法概要

| 步骤 | 脚本 | 输出 |
|------|------|------|
| 下载 PM2.5 | `scripts/00_download_chap.py` | `data/raw/chap_y1k/*.nc` |
| 合并面板 | `scripts/01_build_panel.py` | `data/panel.csv` |
| 描述统计 | `scripts/00_descriptive_analysis.py` | `tables/descriptive_stats.csv`, `figures/fig1_*` |
| 基准 DiD | `scripts/02_did_regression.py` | `tables/did_results.csv`, `figures/fig2_*` |
| 事件研究 | `scripts/03_event_study.py` | `tables/event_study_coef.csv`, `figures/fig3_*` |
| 稳健性 | `scripts/04_robustness.py` | `tables/robustness_results.csv` |

## 一键运行

```powershell
cd Air-Ten-PM25
pip install -r requirements.txt
python scripts/00_download_chap.py
python scripts/01_build_panel.py
python scripts/00_descriptive_analysis.py
python scripts/02_did_regression.py
python scripts/03_event_study.py
python scripts/04_robustness.py
```

论文：`paper/main.tex`（XeLaTeX 编译）。

## 核心模型

**双重差分（TWFE）：**

\[
\ln PM2.5_{ct} = \beta\,(Treat_c \times Post_t) + X_{ct}'\gamma + \alpha_c + \delta_t + \varepsilon_{ct}
\]

**事件研究：** 以 2014 年为基准年（$k=-1$ 省略），估计 $k=-4,\ldots,5$。

- 标准误：城市层面聚类
- 探索性检验见上级目录 `Air-Exploratory/`

## 与 Carbon-Renew / CityEdu 的区别

| | CityEdu-Eco | Carbon-Renew | 本项目 |
|--|-------------|--------------|--------|
| 问题 | 教育 → GDP | 碳交易 → 装机 | **大气十条 → PM2.5** |
| 层级 | 地级市 | 省级 | **地级市** |
| 结果 | 显著 | 不显著 | **显著负向** |

## 数据

详见 `data/DATA_NOTES.md`。
