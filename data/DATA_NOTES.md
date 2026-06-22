# 数据说明

## PM2.5

- **来源：** ChinaHighPM2.5（CHAP）Y1K V4 年度 1km 栅格
- **仓库：** Zenodo record 6398971（Wei & Li 团队）
- **脚本：** `scripts/00_download_chap.py` 自动下载 2010–2019 年 NetCDF
- **提取：** 在 `scripts/01_build_panel.py` 中按 `CityEdu-Eco/data/china_cities.geojson` 地级市质心最近邻采样

## 政策处理组

- **政策：** 《大气污染防治行动计划》（大气十条，2013 年 9 月发布）
- **处理组定义：** `data/appcap_regions.csv`
  - 京津冀：北京、天津、河北全部地级市
  - 长三角：上海、江苏、浙江、安徽全部地级市
  - 珠三角：广州、深圳、珠海、佛山、惠州、东莞、中山、江门、肇庆
- **Post：** 2014 年起 = 1（2013 年为政策发布年，首个完整执行年取 2014）

## 控制变量

- **来源：** `CityEdu-Eco/data/panel.csv`（中国城市统计年鉴整理）
- **变量：** ln(人均GDP)、第二/三产业比重、ln(财政收入)
- **匹配：** 按 `city_key` + `year` 左连接；部分城市年份缺失将在回归中 listwise 删除

## 样本量

- 约 367 个地级行政区 × 10 年；与 CityEdu 交集后有效回归样本略少（取决于经济变量缺失）

## 注意事项

1. CHAP 为卫星/模型融合产品，非地面监测站原始数据；与监测站研究结论方向应一致但系数不可直接对比。
2. 2013 年处理组 PM2.5 偏高（冬季重污染等），稳健性检验含剔除 2013 年。
3. 若 Zenodo 下载失败，可将 `Air-Exploratory/data/raw/chap_y1k/` 中已有文件复制到 `data/raw/chap_y1k/`。
