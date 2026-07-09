# 西安市新能源汽车充电设施供需匹配与选址优化系统

## 项目简介

本系统基于 Streamlit 构建，旨在分析西安市新能源汽车充电设施的空间分布特征，量化供需匹配状况，并通过优化算法为新增充电站选址提供决策支持。

## 快速启动

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
streamlit run app.py
```

浏览器访问 **http://localhost:8501**。

### 运行分析管道（命令行）

```bash
cd src
python run_all.py
```

执行完毕后所有结果输出至 `output/` 目录。

## 功能模块

### 任务一：空间分布测度
- **充电站分布图**：展示西安市所有充电站的位置分布
- **区县密度图**：展示各区县充电站分布密度
- **运营商统计图**：统计各运营商充电站数量

### 任务二：供需匹配量化
- **网格供需得分图**：基于高斯距离衰减的供需匹配得分分布
- **冷热点分析图**：识别供需热点和冷点区域
- **服务盲区地图**：识别供给不足的网格区域

### 任务三：选址优化
- **优化前后对比图**：对比现有站点与新增站点分布
- **新增站点地图**：展示优化算法筛选出的新增站点位置
- **指标对比表**：量化评估选址优化效果

## 项目文件结构

```
YAOSU/
├── app.py                     # Streamlit 交互式 Web 应用（主入口）
├── main.py                    # 系统入口文件
├── launcher.py                # 一键启动脚本
├── README.md                  # 项目说明文档
├── requirements.txt           # Python 依赖清单
├── .gitignore                 # Git 忽略规则
├── data/                      # 处理后数据
│   ├── charging_stations_clean.csv
│   └── charging_stations_xian.geojson
├── src/                       # 核心源代码
│   ├── 00_config.py               # 全局配置
│   ├── 01_preprocess_poi.py       # POI 数据预处理
│   ├── 02_spatial_matching.py     # 空间匹配
│   ├── 03_regional_analysis.py    # 区域分析
│   ├── 04_supply_demand_model.py  # 供需匹配模型
│   ├── 05_location_optimization.py # 选址优化
│   ├── 06_evaluation.py           # 效果评估
│   ├── 07_generate_report.py      # 报告生成
│   ├── run_all.py                 # 一键运行全部模块
│   └── utils.py                   # 通用工具函数
└── output/                    # 运行产物（图表、表格、GeoJSON），gitignore 排除
```

## 数据文件

以下数据文件位于项目根目录：

| 文件 | 说明 |
|------|------|
| `西安市.csv` | POI 兴趣点数据 |
| `西安市.geojson` | 西安市地理边界 |
| `西安市_wgs84.shp` | 道路网络 Shapefile（WGS84 坐标系） |
| `区县.shp` | 全国区县级行政区划边界 |
| `西安市区县.geojson` | 西安市区县边界 GeoJSON |
| `陕西省_西安市_2024.shp` | 西安市人口分布数据 |

## 环境要求

- Python 3.9+
- 依赖库见 `requirements.txt`

## 算法说明

### 供需匹配模型（高斯距离衰减 + 对数饱和）

采用基于高斯距离衰减的单步可达性分析方法：

\[
W_{ij} = \exp\left(-\frac{d_{ij}^{2}}{2d_0^{2}}\right)
\]

其中 \(d_0\) 为用户设定的搜索半径（默认 5000m）；超过搜索半径的衰减权重直接置零。

每个网格的可达供给为所有充电站供给的加权求和：

\[
\text{可达供给}_i = \sum_j W_{ij} \cdot S_j
\]

供需比定义为可达供给与需求量的比值：

\[
\text{供需比}_i = \frac{\text{可达供给}_i}{\text{需求量}_i + 10^{-6}}
\]

供需得分采用对数饱和函数，将任意正供需比映射到 \((0, 1)\) 区间：

\[
\text{供需得分}_i = 1 - \frac{1}{1 + \ln\left(1 + \text{供需比}_i + 10^{-3}\right)}
\]

### 选址优化

- **最大覆盖模型**：整数规划（PuLP + CBC 求解器）求解最优站点位置
- **贪心算法**：快速启发式算法，作为整数规划的后备方案

## 技术特点

1. **性能优化**：使用 `@st.cache_data` 缓存大计算，添加进度条
2. **坐标系管理**：自动处理 WGS84 与 UTM（EPSG:32649）投影转换
3. **三级空间匹配**：within → intersects → cKDTree 最近邻，实现充电站区县归属 100% 匹配
4. **双引擎选址**：整数规划 + 贪心算法自适应切换
5. **交互式参数调节**：支持搜索半径、阈值等参数动态调整
