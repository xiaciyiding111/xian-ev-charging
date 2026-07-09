"""
选址优化模块
使用贪婪算法进行充电站选址优化
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
from utils import read_geojson_without_fiona, cdist_haversine

SEED = config.SEED
BOUNDARY_FILE = config.BOUNDARY_FILE
DATA_DIR = config.DATA_DIR
OUTPUT_DIR = config.OUTPUT_DIR
ROAD_FILE = config.ROAD_FILE
NEW_SITES_COUNT = config.NEW_SITES_COUNT
MIN_DISTANCE_EXISTING = config.MIN_DISTANCE_EXISTING
COVER_THRESHOLD = config.COVER_THRESHOLD

np.random.seed(SEED)

def generate_candidates(blind_spots, charging_gdf, num_candidates=50):
    """
    生成候选点
    
    参数:
        blind_spots: 服务盲区GeoDataFrame
        charging_gdf: 现有充电站GeoDataFrame
        num_candidates: 候选点数量
    
    返回:
        候选点DataFrame
    """
    candidates = []
    
    if len(blind_spots) > 0:
        candidates.extend(list(zip(blind_spots['lon'], blind_spots['lat'])))
    
    if len(candidates) < num_candidates:
        if ROAD_FILE and ROAD_FILE.exists():
            try:
                roads = gpd.read_file(ROAD_FILE)
                roads = roads.to_crs(epsg=4326)
                for geom in roads.geometry:
                    if len(candidates) >= num_candidates:
                        break
                    if geom.geom_type == 'LineString':
                        coords = list(geom.coords)
                        for i in range(len(coords)):
                            if len(candidates) >= num_candidates:
                                break
                            candidates.append(coords[i])
            except Exception as e:
                print(f"读取路网失败: {e}")
        
        if len(candidates) < num_candidates:
            min_lon, min_lat, max_lon, max_lat = blind_spots.total_bounds
            while len(candidates) < num_candidates:
                lon = np.random.uniform(min_lon, max_lon)
                lat = np.random.uniform(min_lat, max_lat)
                candidates.append((lon, lat))
    
    candidates = pd.DataFrame(candidates[:num_candidates], columns=['lon', 'lat'])
    candidates['candidate_id'] = candidates.index
    
    return candidates

def greedy_p_median(demand_points, candidates, existing_sites, k=5, min_distance=500):
    """
    贪婪P-Median算法
    
    参数:
        demand_points: 需求点DataFrame
        candidates: 候选点DataFrame
        existing_sites: 现有站点DataFrame
        k: 新增站点数量
        min_distance: 与现有站点最小距离
    
    返回:
        选中的站点DataFrame
    """
    demand_coords = demand_points[['lon', 'lat']].values
    candidate_coords = candidates[['lon', 'lat']].values
    existing_coords = existing_sites[['lon', 'lat']].values
    
    # 计算候选点到现有站点的距离
    dist_candidate_existing = cdist_haversine(candidate_coords, existing_coords)
    min_dist_to_existing = dist_candidate_existing.min(axis=1)
    
    # 筛选有效候选点
    valid_mask = np.where(min_dist_to_existing >= min_distance)[0]
    
    if len(valid_mask) < k:
        print(f"警告：有效候选点不足{k}个，使用全部有效候选点")
        valid_mask = np.arange(min(len(candidates), k))
    
    valid_candidates = candidate_coords[valid_mask]
    valid_indices = valid_mask
    
    # 计算需求点到候选点的距离
    dist_demand_candidate = cdist_haversine(demand_coords, valid_candidates)
    
    # 贪婪选择
    selected_indices = []
    selected_coords = []
    
    for _ in range(min(k, len(valid_candidates))):
        best_idx = -1
        best_coverage = -np.inf
        
        for i in range(len(valid_candidates)):
            if i in selected_indices:
                continue
            
            # 计算新增此候选点后的覆盖需求
            temp_selected = selected_coords + [valid_candidates[i]]
            if len(temp_selected) == 0:
                continue
            
            temp_coords = np.array(temp_selected)
            dists = cdist_haversine(demand_coords, temp_coords)
            min_dists = dists.min(axis=1)
            
            # 计算加权覆盖
            weights = demand_points['demand'].values
            coverage = np.sum(weights * (min_dists <= COVER_THRESHOLD))
            
            if coverage > best_coverage:
                best_coverage = coverage
                best_idx = i
        
        if best_idx != -1:
            selected_indices.append(best_idx)
            selected_coords.append(valid_candidates[best_idx])
    
    selected_candidates = candidates.iloc[valid_indices[selected_indices]].copy()
    
    return selected_candidates

def main():
    """
    主函数：选址优化
    """
    print("=" * 50)
    print("选址优化开始")
    print("=" * 50)
    
    print("读取边界数据...")
    boundary = read_geojson_without_fiona(BOUNDARY_FILE)
    
    print("读取充电站数据...")
    charging_gdf = read_geojson_without_fiona(DATA_DIR / "charging_stations_xian.geojson")
    
    print("读取服务盲区...")
    blind_spots = read_geojson_without_fiona(OUTPUT_DIR / "service_blind_spots.geojson")
    
    print("读取需求网格...")
    grid = read_geojson_without_fiona(OUTPUT_DIR / "grid_supply_demand.geojson")
    
    print("生成候选点...")
    candidates = generate_candidates(blind_spots, charging_gdf)
    print(f"候选点数量: {len(candidates)}")
    
    print("贪婪P-Median选址优化...")
    selected_sites = greedy_p_median(grid, candidates, charging_gdf, k=NEW_SITES_COUNT, min_distance=MIN_DISTANCE_EXISTING)
    print(f"选中站点数量: {len(selected_sites)}")
    
    selected_sites['ports'] = 6
    selected_sites.to_csv(OUTPUT_DIR / "new_sites.csv", index=False, encoding='utf-8-sig')
    print(f"输出新增站点: {OUTPUT_DIR / 'new_sites.csv'}")
    
    print("绘制优化结果图...")
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    boundary.plot(ax=ax, color='lightgray', edgecolor='black')
    grid.plot(ax=ax, column='score_norm', cmap='RdYlBu_r', alpha=0.5, legend=False)
    charging_gdf.plot(ax=ax, marker='o', color='blue', markersize=10, label='现有站点')
    
    if len(selected_sites) > 0:
        selected_sites.plot(ax=ax, x='lon', y='lat', marker='*', color='red', markersize=150, label='新增站点')
    
    plt.title('西安市充电站选址优化结果图', fontsize=14)
    plt.legend()
    plt.axis('off')
    plt.savefig(OUTPUT_DIR / "optimization_map.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"输出优化图: {OUTPUT_DIR / 'optimization_map.png'}")
    
    print("=" * 50)
    print("选址优化完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
