"""
供需匹配模型模块
实现两步移动搜索法（2SFCA）进行供需匹配分析
"""
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import sys
import importlib
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
config = importlib.import_module('00_config')
from utils import read_geojson_without_fiona, save_geojson, create_grid, cdist_haversine, simple_pca

SEED = config.SEED
BOUNDARY_FILE = config.BOUNDARY_FILE
RAW_POI_FILE = config.RAW_POI_FILE
OUTPUT_DIR = config.OUTPUT_DIR
SEARCH_RADIUS = config.SEARCH_RADIUS
GRID_SIZE = config.GRID_SIZE
POPULATION_FILE = config.POPULATION_FILE
PLACE_TYPE_MAP = config.PLACE_TYPE_MAP
WEIGHTS = config.WEIGHTS
DATA_DIR = config.DATA_DIR

np.random.seed(SEED)

def extract_place_type(type_str):
    """
    从类型字符串中提取场所类型
    
    参数:
        type_str: 类型字符串
    
    返回:
        场所类型
    """
    type_str = str(type_str)
    for place_type, keywords in PLACE_TYPE_MAP.items():
        for kw in keywords:
            if kw in type_str:
                return place_type
    return "其他"

def two_stage_fca(grid_coords, supplies, charging_coords, search_radius):
    """
    两步移动搜索法（2SFCA）
    
    参数:
        grid_coords: 网格中心点坐标
        supplies: 各充电站供给量（端口数）
        charging_coords: 充电站坐标
        search_radius: 搜索半径（米）
    
    返回:
        各网格的供需匹配得分
    """
    dists = cdist_haversine(grid_coords, charging_coords)
    
    # 高斯衰减函数
    stage1_weights = np.where(dists <= search_radius, np.exp(-0.5 * (dists / search_radius)**2), 0)
    
    # 第一步：供给方搜索，计算每个充电站的供需比
    Rj = supplies / (stage1_weights.sum(axis=0) + 1e-10)
    
    # 第二步：需求方搜索，计算每个需求点的可达性得分
    stage2_weights = np.where(dists <= search_radius, np.exp(-0.5 * (dists / search_radius)**2) * Rj, 0)
    scores = stage2_weights.sum(axis=1)
    
    return scores

def calculate_morans_i(values, coords, k=8):
    """
    计算全局Moran's I指数
    
    参数:
        values: 变量值数组
        coords: 坐标数组
        k: 最近邻数量
    
    返回:
        Moran's I值
    """
    n = len(values)
    dists = cdist_haversine(coords, coords)
    knn_indices = np.argsort(dists, axis=1)[:, 1:k+1]
    
    mean_val = np.mean(values)
    var_val = np.var(values)
    if var_val == 0:
        return 0
    
    w_sum = 0
    s0 = 0
    
    for i in range(n):
        neighbors = knn_indices[i]
        for j in neighbors:
            w = 1 / (dists[i, j] + 1e-10)
            w_sum += w * (values[i] - mean_val) * (values[j] - mean_val)
            s0 += w
    
    if s0 == 0:
        return 0
    
    moran_i = (n / s0) * (w_sum / (n * var_val))
    return moran_i

def calculate_gis(values, coords, k=8):
    """
    计算Getis-Ord Gi*统计量
    
    参数:
        values: 变量值数组
        coords: 坐标数组
        k: 最近邻数量
    
    返回:
        Gi*值数组
    """
    n = len(values)
    dists = cdist_haversine(coords, coords)
    knn_indices = np.argsort(dists, axis=1)[:, 1:k+1]
    
    mean_val = np.mean(values)
    
    gi_values = []
    for i in range(n):
        neighbors = knn_indices[i]
        weights = 1 / (dists[i, neighbors] + 1e-10)
        w_sum_w = np.sum(weights)
        if w_sum_w == 0:
            gi_values.append(0)
            continue
        
        weighted_sum = np.sum(weights * values[neighbors])
        numerator = weighted_sum - mean_val * w_sum_w
        denominator = np.std(values) * np.sqrt((n * np.sum(weights ** 2) - w_sum_w ** 2) / (n - 1))
        
        gi_values.append(numerator / denominator if denominator != 0 else 0)
    
    return np.array(gi_values)

def main():
    """
    主函数：供需匹配分析
    """
    print("=" * 50)
    print("供需匹配模型开始运行")
    print("=" * 50)
    
    try:
        print("读取边界数据...")
        boundary = read_geojson_without_fiona(BOUNDARY_FILE)
        print(f"  边界数据读取成功: {len(boundary)} 个区")

        print("读取充电站数据...")
        charging_gdf = read_geojson_without_fiona(DATA_DIR / "charging_stations_xian.geojson")
        charging_gdf['ports'] = charging_gdf['ports'].fillna(3)
        print(f"  充电站数据读取成功: {len(charging_gdf)} 个站")

        print("读取POI数据...")
        df = pd.read_csv(RAW_POI_FILE, encoding='utf-8-sig')
        
        # 检测类型列
        type_cols = []
        for col in df.columns:
            if '类型' in str(col) or '分类' in str(col) or '大类' in str(col) or '中类' in str(col):
                type_cols.append(col)
        
        if type_cols:
            df['type'] = df[type_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
        else:
            df['type'] = ''
        print(f"  POI数据读取成功: {len(df)} 条记录")

        print("创建网格...")
        grid = create_grid(boundary, GRID_SIZE, max_cells=3000)
        print(f"  网格创建成功: {len(grid)} 个网格单元")

        print("计算需求指数...")
        poi_types = df[['lon', 'lat', 'type']].copy()
        poi_types['place_type'] = poi_types['type'].apply(lambda x: extract_place_type(x))
        
        demand_features = pd.DataFrame()
        grid_coords = grid[['lon', 'lat']].values

        for place_type in PLACE_TYPE_MAP.keys():
            mask = poi_types['place_type'] == place_type
            subset = poi_types[mask]
            if len(subset) == 0:
                demand_features[place_type] = 0
                continue
            coords_poi = subset[['lon', 'lat']].values
            dists = cdist_haversine(grid_coords, coords_poi)
            kernel = np.exp(-0.5 * (dists / 1000)**2)
            demand_features[place_type] = kernel.sum(axis=1)

        if demand_features.empty:
            grid['demand'] = 1
        else:
            demand_features_norm = (demand_features - demand_features.mean()) / (demand_features.std() + 1e-10)
            grid['demand'] = simple_pca(demand_features_norm.values, n_components=1).flatten()
            grid['demand'] = (grid['demand'] - grid['demand'].min()) / (grid['demand'].max() - grid['demand'].min() + 1e-10)
        print("  需求指数计算成功")

        print("计算供给量...")
        grid['supply'] = 0
        charging_coords = charging_gdf[['lon', 'lat']].values
        supplies = charging_gdf['ports'].values
        
        for i, row in enumerate(charging_gdf.itertuples()):
            dists = cdist_haversine([[row.lon, row.lat]], grid_coords)
            mask = dists[0] < GRID_SIZE / 2
            grid.loc[mask, 'supply'] += row.ports
        print("  供给量计算成功")

        print("计算2SFCA得分...")
        sensitivity_results = []
        for radius in SEARCH_RADIUS:
            scores = two_stage_fca(grid_coords, supplies, charging_coords, radius)
            grid[f'score_{radius}'] = scores
            sensitivity_results.append({
                'radius': radius,
                'mean_score': float(scores.mean()),
                'std_score': float(scores.std()),
                'min_score': float(scores.min()),
                'max_score': float(scores.max())
            })
            print(f"  半径 {radius}m: 平均得分={scores.mean():.4f}")

        grid['score'] = grid[f'score_{SEARCH_RADIUS[1]}']
        grid['score_norm'] = (grid['score'] - grid['score'].min()) / (grid['score'].max() - grid['score'].min() + 1e-10)

        pd.DataFrame(sensitivity_results).to_csv(OUTPUT_DIR / "sensitivity_analysis.csv", index=False, encoding='utf-8-sig')
        print(f"  输出敏感性分析结果")

        print("计算Moran's I...")
        moran_i = calculate_morans_i(grid['score_norm'].values, grid_coords)
        print(f"  Moran's I: {moran_i:.4f}")

        print("冷热点分析...")
        gi_values = calculate_gis(grid['score_norm'].values, grid_coords)
        grid['gi'] = gi_values
        grid['hotspot'] = np.digitize(gi_values, np.percentile(gi_values, [25, 50, 75])) + 1
        print("  冷热点分析成功")

        save_geojson(grid, OUTPUT_DIR / "grid_supply_demand.geojson")
        print(f"  输出网格供需得分: grid_supply_demand.geojson")

        print("绘制供需分布图...")
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        boundary.plot(ax=ax, color='lightgray', edgecolor='black')
        grid.plot(ax=ax, column='score_norm', cmap='RdYlBu_r', legend=True,
                  legend_kwds={'label': '供需匹配得分', 'orientation': 'horizontal'})
        charging_gdf.plot(ax=ax, marker='o', color='black', markersize=5)
        plt.title('西安市充电站供需匹配得分空间分布图', fontsize=14)
        plt.axis('off')
        plt.savefig(OUTPUT_DIR / "supply_demand_map.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  输出供需分布图: supply_demand_map.png")

        print("绘制冷热点图...")
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        boundary.plot(ax=ax, color='lightgray', edgecolor='black')
        hotspot_colors = {1: 'blue', 2: 'lightblue', 3: 'orange', 4: 'red'}
        for q in sorted(grid['hotspot'].unique()):
            subset = grid[grid['hotspot'] == q]
            subset.plot(ax=ax, color=hotspot_colors.get(q, 'gray'), alpha=0.6)
        plt.title('西安市充电站供需冷热点分析图（Getis-Ord Gi*）', fontsize=14)
        plt.legend(['冷点', '次冷点', '次热点', '热点'], bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.axis('off')
        plt.savefig(OUTPUT_DIR / "hotspot_map.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  输出冷热点图: hotspot_map.png")

        print("识别服务盲区...")
        threshold = grid['score_norm'].quantile(0.2)
        blind_spots = grid[grid['score_norm'] <= threshold]
        save_geojson(blind_spots, OUTPUT_DIR / "service_blind_spots.geojson")
        print(f"  输出服务盲区: service_blind_spots.geojson (共{len(blind_spots)}个)")

        print("=" * 50)
        print("供需匹配模型完成!")
        print("=" * 50)

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
