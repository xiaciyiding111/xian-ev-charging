"""
效果评估模块
评估优化前后的各项指标并进行对比分析
"""
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import importlib
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
config = importlib.import_module('00_config')
from utils import read_geojson_without_fiona, cdist_haversine, calculate_gini

DATA_DIR = config.DATA_DIR
OUTPUT_DIR = config.OUTPUT_DIR
GRID_SIZE = config.GRID_SIZE
COVER_THRESHOLD = config.COVER_THRESHOLD

def calculate_metrics(grid, charging_sites, demand_col='demand', coverage_radius=5000):
    """
    计算评估指标
    
    参数:
        grid: 需求网格GeoDataFrame
        charging_sites: 充电站DataFrame
        demand_col: 需求列名
        coverage_radius: 覆盖半径（米）
    
    返回:
        指标字典
    """
    demand_coords = grid[['lon', 'lat']].values
    site_coords = charging_sites[['lon', 'lat']].values
    
    if len(site_coords) == 0:
        return {'avg_distance': np.inf, 'coverage': 0, 'gini': 1}
    
    dists = cdist_haversine(demand_coords, site_coords)
    min_dists = dists.min(axis=1)
    
    weights = grid[demand_col].values
    avg_distance = np.average(min_dists, weights=weights)
    coverage = np.sum(weights * (min_dists <= coverage_radius)) / np.sum(weights) * 100
    
    supply_counts = np.zeros(len(grid))
    for _, row in charging_sites.iterrows():
        dists = cdist_haversine([[row['lon'], row['lat']]], demand_coords)
        mask = dists[0] < GRID_SIZE / 2
        supply_counts[mask] += row.get('ports', 1)
    
    gini = calculate_gini(supply_counts)
    
    return {
        'avg_distance': avg_distance,
        'coverage': coverage,
        'gini': gini
    }

def main():
    """
    主函数：效果评估
    """
    print("=" * 50)
    print("效果评估开始")
    print("=" * 50)
    
    print("读取需求网格...")
    grid = read_geojson_without_fiona(OUTPUT_DIR / "grid_supply_demand.geojson")
    grid['demand'] = grid.get('demand', 1)
    
    print("读取现有充电站...")
    charging_gdf = read_geojson_without_fiona(DATA_DIR / "charging_stations_xian.geojson")
    
    print("读取新增站点...")
    new_sites = pd.read_csv(OUTPUT_DIR / "new_sites.csv", encoding='utf-8-sig')
    new_sites['ports'] = new_sites.get('ports', 6)
    
    print("计算优化前指标...")
    metrics_before = calculate_metrics(grid, charging_gdf)
    print(f"优化前 - 平均距离: {metrics_before['avg_distance']:.2f}m, 覆盖率: {metrics_before['coverage']:.2f}%, 基尼系数: {metrics_before['gini']:.4f}")
    
    print("计算优化后指标...")
    all_sites = pd.concat([charging_gdf[['lon', 'lat', 'ports']], new_sites[['lon', 'lat', 'ports']]], ignore_index=True)
    metrics_after = calculate_metrics(grid, all_sites)
    print(f"优化后 - 平均距离: {metrics_after['avg_distance']:.2f}m, 覆盖率: {metrics_after['coverage']:.2f}%, 基尼系数: {metrics_after['gini']:.4f}")
    
    comparison = pd.DataFrame({
        '指标': ['平均可达距离(m)', '覆盖率(%)', '基尼系数'],
        '优化前': [metrics_before['avg_distance'], metrics_before['coverage'], metrics_before['gini']],
        '优化后': [metrics_after['avg_distance'], metrics_after['coverage'], metrics_after['gini']],
        '变化量': [
            metrics_after['avg_distance'] - metrics_before['avg_distance'],
            metrics_after['coverage'] - metrics_before['coverage'],
            metrics_after['gini'] - metrics_before['gini']
        ],
        '变化率(%)': [
            (metrics_after['avg_distance'] - metrics_before['avg_distance']) / metrics_before['avg_distance'] * 100 if metrics_before['avg_distance'] > 0 else 0,
            (metrics_after['coverage'] - metrics_before['coverage']) / metrics_before['coverage'] * 100 if metrics_before['coverage'] > 0 else 0,
            (metrics_after['gini'] - metrics_before['gini']) / metrics_before['gini'] * 100 if metrics_before['gini'] > 0 else 0
        ]
    })
    
    comparison.to_csv(OUTPUT_DIR / "comparison_table.csv", index=False, encoding='utf-8-sig')
    print(f"输出对比表: {OUTPUT_DIR / 'comparison_table.csv'}")
    
    print("绘制对比柱状图...")
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    comparison_melt = comparison.melt(id_vars='指标', value_vars=['优化前', '优化后'])
    sns.barplot(data=comparison_melt, x='指标', y='value', hue='variable', palette=['blue', 'green'])
    plt.title('优化前后指标对比', fontsize=14)
    plt.xlabel('指标', fontsize=12)
    plt.ylabel('数值', fontsize=12)
    plt.legend(title='状态')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "comparison_chart.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"输出对比图: {OUTPUT_DIR / 'comparison_chart.png'}")
    
    print("绘制雷达图...")
    labels = ['覆盖率', '可达性', '均衡性']
    before = [metrics_before['coverage']/100, 1 - metrics_before['avg_distance']/10000, 1 - metrics_before['gini']]
    after = [metrics_after['coverage']/100, 1 - metrics_after['avg_distance']/10000, 1 - metrics_after['gini']]
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    before += before[:1]
    after += after[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'polar': True})
    ax.fill(angles, before, 'blue', alpha=0.25)
    ax.fill(angles, after, 'green', alpha=0.25)
    ax.plot(angles, before, 'blue', linewidth=2, label='优化前')
    ax.plot(angles, after, 'green', linewidth=2, label='优化后')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title('优化前后综合指标对比', fontsize=14)
    plt.legend()
    plt.savefig(OUTPUT_DIR / "radar_chart.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"输出雷达图: {OUTPUT_DIR / 'radar_chart.png'}")
    
    print("=" * 50)
    print("效果评估完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
