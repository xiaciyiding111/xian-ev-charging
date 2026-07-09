"""
报告生成模块
生成最终分析报告
"""
import pandas as pd
import numpy as np
import sys
import importlib
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
config = importlib.import_module('00_config')
from utils import df_to_markdown

BASE_DIR = config.BASE_DIR
OUTPUT_DIR = config.OUTPUT_DIR
CHARGING_KEYWORDS = config.CHARGING_KEYWORDS
MIN_DISTANCE_EXISTING = config.MIN_DISTANCE_EXISTING
ROAD_FILE = config.ROAD_FILE
POPULATION_FILE = config.POPULATION_FILE

def main():
    """
    主函数：生成分析报告
    """
    print("=" * 50)
    print("报告生成开始")
    print("=" * 50)
    
    print("读取分析结果...")
    
    district_stats = pd.read_csv(OUTPUT_DIR / "district_stats.csv", encoding='utf-8-sig')
    operator_stats = pd.read_csv(OUTPUT_DIR / "operator_stats.csv", encoding='utf-8-sig')
    sensitivity = pd.read_csv(OUTPUT_DIR / "sensitivity_analysis.csv", encoding='utf-8-sig')
    comparison = pd.read_csv(OUTPUT_DIR / "comparison_table.csv", encoding='utf-8-sig')
    new_sites = pd.read_csv(OUTPUT_DIR / "new_sites.csv", encoding='utf-8-sig')
    
    coverage_improvement = comparison[comparison['指标'] == '覆盖率(%)']['变化量'].values[0]
    gini_improvement = comparison[comparison['指标'] == '基尼系数']['变化量'].values[0]
    distance_improvement = comparison[comparison['指标'] == '平均可达距离(m)']['变化量'].values[0]
    
    report = f"""# 西安市新能源汽车充电设施供需匹配与选址优化报告

## 一、项目背景与目标

本项目针对西安市新能源汽车充电设施进行供需匹配分析与选址优化，旨在：
- 分析现有充电站的空间分布特征
- 评估各区域的供需匹配状况
- 识别服务盲区
- 优化新增充电站选址

## 二、数据来源与预处理

### 2.1 数据来源
| 数据类型 | 文件路径 | 说明 |
|---------|---------|------|
| POI数据 | `西安市.csv` | 包含充电站及各类兴趣点 |
| 行政区划边界 | `西安市_wgs84.geojson` | WGS84坐标系区县级面要素 |
| 区县边界 | `区县.shp` | 全国区县级行政区划数据 |
| 路网数据 | `西安市_wgs84.shp` | 西安市道路网络数据 |
| 人口分布 | `陕西省_西安市_2024.shp` | 西安市人口分区数据 |

### 2.2 数据预处理说明
- **路网数据**：{f"使用文件: {ROAD_FILE.name}" if ROAD_FILE and ROAD_FILE.exists() else "未提供，使用球面距离(Haversine)替代"}
- **人口栅格**：{f"使用文件: {POPULATION_FILE.name}" if POPULATION_FILE and POPULATION_FILE.exists() else "未提供，使用POI密度作为需求代理"}

### 2.3 充电站筛选规则
类型或名称包含以下关键词：{', '.join(CHARGING_KEYWORDS)}

## 三、技术路线

```
数据输入 → POI预处理 → 空间匹配 → 供需分析 → 选址优化 → 效果验证
```

## 四、方法详述

### 4.1 两步移动搜索法（2SFCA）

2SFCA是一种经典的空间可达性分析方法，本研究改进之处：

**第一步（供给方搜索）：**
- 对每个供给点j，搜索半径d0内的所有需求点
- 累加需求权重，计算供需比 Rj = Sj / ΣWij

**第二步（需求方搜索）：**
- 对每个需求点i，搜索半径d0内的所有供给点
- 加权求和供需比得到可达性得分 Ai = ΣRj * Wij

**距离衰减函数：**
采用高斯衰减函数：exp(-0.5 * (d/d0)^2)

### 4.2 贪婪P-Median选址模型

**目标函数：**
最大化加权需求覆盖率（权重为需求指数）

**约束条件：**
- 新增站点数量约束：k = {config.NEW_SITES_COUNT}
- 与现有站点距离约束：≥ {MIN_DISTANCE_EXISTING}m
- 覆盖阈值距离：{config.COVER_THRESHOLD}m

## 五、实验结果

### 5.1 充电站空间分布

![充电站空间分布图](output/distribution_map.png)

### 5.2 区县级密度分布

![区县密度图](output/district_choropleth.png)

### 5.3 区县统计

{df_to_markdown(district_stats[['区县', 'count', 'avg_ports', 'density']], floatfmt='.2f')}

### 5.4 运营商分析

![运营商分布](output/operator_bar.png)

### 5.5 运营商统计

{df_to_markdown(operator_stats[['operator', 'count', 'total_ports', 'percentage']], floatfmt='.2f')}

### 5.6 供需匹配得分

![供需分布图](output/supply_demand_map.png)

### 5.7 冷热点分析

![冷热点图](output/hotspot_map.png)

### 5.8 参数敏感性分析

{df_to_markdown(sensitivity, floatfmt='.4f')}

## 六、选址优化结果

### 6.1 新增站点位置

{df_to_markdown(new_sites[['lon', 'lat', 'ports']], floatfmt='.6f')}

### 6.2 优化结果图

![优化结果](output/optimization_map.png)

## 七、效果验证与量化对比

### 7.1 指标对比表

{df_to_markdown(comparison, floatfmt='.2f')}

### 7.2 对比图表

![对比柱状图](output/comparison_chart.png)
![雷达图](output/radar_chart.png)

## 八、结论与政策建议

### 8.1 主要结论

1. **覆盖率提升**：优化后5km覆盖率提升约{coverage_improvement:.2f}个百分点
2. **可达性改善**：平均可达距离减少约{abs(distance_improvement):.0f}米
3. **均衡性变化**：基尼系数{('下降' if gini_improvement < 0 else '上升')}约{abs(gini_improvement):.4f}

### 8.2 政策建议

1. **优先建设区域**：建议优先在服务盲区（供需得分最低的20%区域）建设充电站
2. **运营商合作**：鼓励不同运营商在盲区区域合作共建共享
3. **规划指引**：将充电站规划纳入城市总体规划，确保合理布局
4. **动态监测**：建立充电设施供需监测体系，定期评估和调整

---

**报告生成时间**：自动生成
**项目版本**：1.0
"""
    
    with open(BASE_DIR / "final_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"输出报告: {BASE_DIR / 'final_report.md'}")
    print("=" * 50)
    print("报告生成完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
