# 西安市新能源汽车充电设施供需匹配与选址优化系统

## 项目简介

本系统基于 Streamlit 构建，旨在分析西安市新能源汽车充电设施的空间分布特征，量化供需匹配状况，并通过优化算法为新增充电站选址提供决策支持。

## 快速启动

### 方式一：一键启动（推荐）

双击项目根目录下的 **`YAOSU启动器.exe`**，服务将自动启动并打开浏览器。

> 使用前提：电脑已安装 Python 3.9+ 及项目依赖（见下方"安装依赖"）。

### 方式二：命令行启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
streamlit run app.py
```

浏览器访问 **http://localhost:8501**。

### 运行分析管道（命令行，不启动网页）

```bash
cd src
python run_all.py
```

执行完毕后所有结果输出至 `output/` 目录，最终报告生成为 `final_report.md`。

## 功能模块

### 任务一：空间分布测度
- **充电站分布图**：展示西安市所有充电站的位置分布
- **区县密度图**：展示各区县充电站分布密度
- **运营商统计图**：统计各运营商充电站数量

### 任务二：供需匹配量化
- **网格供需得分图**：基于 2SFCA 模型计算的 1km×1km 网格供需匹配得分
- **冷热点分析图**：识别供需热点和冷点区域
- **服务盲区地图**：识别供给不足的网格区域

### 任务三：选址优化
- **优化前后对比图**：对比现有站点与新增站点分布
- **新增站点地图**：展示优化算法筛选出的新增站点位置
- **指标对比表**：量化评估选址优化效果

## 项目文件结构

```
YAOSU/
├── app.py                  # Streamlit 交互式 Web 应用（主入口）
├── main.py                 # 系统入口文件
├── launcher.py             # 一键启动脚本
├── YAOSU启动器.exe          # 一键启动可执行文件
├── README.md               # 项目说明文档
├── final_report.md         # 最终分析报告
├── requirements.txt        # Python 依赖清单
├── data/                   # 数据文件目录
│   ├── charging_stations_raw.csv
│   ├── charging_stations_clean.csv
│   └── charging_stations_xian.geojson
├── src/                    # 核心源代码
│   ├── 00_config.py        # 全局配置（路径、参数、关键词）
│   ├── 01_preprocess_poi.py    # POI 数据预处理
│   ├── 02_spatial_matching.py  # 空间匹配
│   ├── 03_regional_analysis.py # 区域分析
│   ├── 04_supply_demand_model.py   # 供需匹配模型（2SFCA）
│   ├── 05_location_optimization.py # 选址优化
│   ├── 06_evaluation.py           # 效果评估
│   ├── 07_generate_report.py      # 报告生成
│   ├── run_all.py            # 一键运行全部模块
│   └── utils.py              # 通用工具函数
├── output/                 # 运行产物（图表、表格、GeoJSON）
└── wheels/                 # 离线依赖包
    └── geopandas-1.1.3-py3-none-any.whl
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

- **2SFCA**：两步移动搜索法，引入高斯距离衰减函数，用于计算网格级供需匹配得分
- **最大覆盖模型**：整数规划（CBC 求解器）求解最优站点位置
- **贪心算法**：快速启发式算法，作为整数规划的后备方案

## 技术特点

1. **性能优化**：使用 `@st.cache_data` 缓存大计算，添加进度条
2. **坐标系管理**：自动处理 WGS84 与 UTM（EPSG:32649）投影转换
3. **三级空间匹配**：within → intersects → cKDTree 最近邻，实现充电站区县归属 100% 匹配
4. **双引擎选址**：整数规划 + 贪心算法自适应切换
5. **交互式参数调节**：支持搜索半径、阈值等参数动态调整
