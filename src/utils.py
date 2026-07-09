"""
工具函数模块
提供空间分析、数据处理等通用功能
"""
import pandas as pd
import numpy as np
import json
from shapely.geometry import Point, Polygon, box, shape, mapping
from shapely.ops import unary_union
import geopandas as gpd

def haversine_distance(lon1, lat1, lon2, lat2):
    """
    计算两点之间的Haversine距离（米）
    
    参数:
        lon1, lat1: 点1的经纬度
        lon2, lat2: 点2的经纬度
    
    返回:
        距离（米）
    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    r = 6371000  # 地球半径（米）
    return c * r

def cdist_haversine(coords1, coords2):
    """
    计算两组坐标之间的距离矩阵（米），纯NumPy向量化实现

    参数:
        coords1: 第一组坐标，shape (n1, 2)
        coords2: 第二组坐标，shape (n2, 2)

    返回:
        距离矩阵，shape (n1, n2)
    """
    coords1 = np.asarray(coords1, dtype=np.float64)
    coords2 = np.asarray(coords2, dtype=np.float64)

    lon1 = np.radians(coords1[:, 0])   # (n1,)
    lat1 = np.radians(coords1[:, 1])   # (n1,)
    lon2 = np.radians(coords2[:, 0])   # (n2,)
    lat2 = np.radians(coords2[:, 1])   # (n2,)

    dlon = lon1[:, np.newaxis] - lon2[np.newaxis, :]   # (n1, n2)
    dlat = lat1[:, np.newaxis] - lat2[np.newaxis, :]   # (n1, n2)

    a = (np.sin(dlat / 2) ** 2
         + np.cos(lat1[:, np.newaxis])
         * np.cos(lat2[np.newaxis, :])
         * np.sin(dlon / 2) ** 2)

    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    return 6371000 * c

def read_geojson_without_fiona(filepath):
    """
    不使用fiona读取GeoJSON文件
    
    参数:
        filepath: 文件路径
    
    返回:
        GeoDataFrame
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data['features']
    geometries = []
    properties = []
    
    for feature in features:
        geom = shape(feature['geometry'])
        geometries.append(geom)
        properties.append(feature['properties'])
    
    gdf = gpd.GeoDataFrame(properties, geometry=geometries, crs="EPSG:4326")
    return gdf

def save_geojson(gdf, filepath):
    """
    保存GeoDataFrame为GeoJSON文件
    
    参数:
        gdf: GeoDataFrame
        filepath: 输出文件路径
    """
    features = []
    for _, row in gdf.iterrows():
        feature = {
            "type": "Feature",
            "properties": row.drop('geometry').to_dict(),
            "geometry": mapping(row['geometry'])
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

def create_grid(boundary, grid_size_m, max_cells=5000):
    """
    创建渔网网格
    
    参数:
        boundary: 边界GeoDataFrame
        grid_size_m: 网格大小（米）
        max_cells: 最大网格数量
    
    返回:
        网格GeoDataFrame
    """
    bounds = boundary.total_bounds
    xmin, ymin, xmax, ymax = bounds
    
    # 将米转换为经纬度单位（约等于111000米/度）
    cell_size = grid_size_m / 111000
    
    x_coords = np.arange(xmin, xmax, cell_size)
    y_coords = np.arange(ymin, ymax, cell_size)
    
    boundary_geom = unary_union(boundary.geometry.tolist())
    
    polygons = []
    centroids = []
    
    for x in x_coords[:-1]:
        for y in y_coords[:-1]:
            cell = box(x, y, x + cell_size, y + cell_size)
            if cell.intersects(boundary_geom):
                polygons.append(cell)
                centroids.append((x + cell_size/2, y + cell_size/2))
                if len(polygons) >= max_cells:
                    break
        if len(polygons) >= max_cells:
            break
    
    grid = gpd.GeoDataFrame({
        'geometry': polygons,
        'lon': [c[0] for c in centroids],
        'lat': [c[1] for c in centroids]
    }, crs="EPSG:4326")
    grid['grid_id'] = range(len(grid))
    
    return grid

def simple_pca(data, n_components=1):
    """
    简单PCA实现（不依赖sklearn）
    
    参数:
        data: 数据矩阵，shape (n_samples, n_features)
        n_components: 主成分数量
    
    返回:
        主成分得分
    """
    data_centered = data - data.mean(axis=0)
    cov_matrix = np.cov(data_centered.T)
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    idx = eigenvalues.argsort()[::-1]
    eigenvectors = eigenvectors[:, idx]
    principal_component = eigenvectors[:, 0]
    scores = data_centered @ principal_component
    return scores.reshape(-1, 1)

def calculate_gini(values):
    """
    计算基尼系数
    
    参数:
        values: 数值数组
    
    返回:
        基尼系数
    """
    values = np.sort(values)
    n = len(values)
    if n == 0 or np.sum(values) == 0:
        return 0
    index = np.arange(1, n + 1)
    gini = (np.sum((2 * index - n - 1) * values)) / (n * np.sum(values))
    return gini

def df_to_markdown(df, floatfmt='.2f'):
    """
    将DataFrame转换为markdown表格
    
    参数:
        df: DataFrame
        floatfmt: 浮点数格式
    
    返回:
        markdown表格字符串
    """
    if len(df) == 0:
        return "无数据"
    
    lines = []
    lines.append("| " + " | ".join(str(col) for col in df.columns) + " |")
    lines.append("| " + " | ".join("---" for _ in df.columns) + " |")
    
    for _, row in df.iterrows():
        row_values = []
        for val in row.values:
            if isinstance(val, float):
                row_values.append(f"{val:{floatfmt}}")
            else:
                row_values.append(str(val))
        lines.append("| " + " | ".join(row_values) + " |")
    
    return "\n".join(lines)
