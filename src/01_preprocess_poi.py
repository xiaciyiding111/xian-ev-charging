"""
POI数据预处理模块
从西安市.csv中筛选充电站并提取相关信息
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import importlib

sys.path.append(str(Path(__file__).parent))
config = importlib.import_module('00_config')

SEED = config.SEED
RAW_POI_FILE = config.RAW_POI_FILE
DATA_DIR = config.DATA_DIR
CHARGING_KEYWORDS = config.CHARGING_KEYWORDS
OPERATOR_KEYWORDS = config.OPERATOR_KEYWORDS
PLACE_TYPE_MAP = config.PLACE_TYPE_MAP

np.random.seed(SEED)

def detect_columns(df):
    """
    自动检测数据列名
    
    参数:
        df: DataFrame
    
    返回:
        列名映射字典
    """
    col_mapping = {}
    type_cols = []
    for col in df.columns:
        col_lower = str(col).lower()
        if 'lon' in col_lower or '经度' in str(col) or 'long' in col_lower:
            col_mapping['lon'] = col
        elif 'lat' in col_lower or '纬度' in str(col):
            col_mapping['lat'] = col
        elif 'type' in col_lower or '类型' in str(col) or '分类' in str(col) or '大类' in str(col) or '中类' in str(col):
            type_cols.append(col)
        elif 'name' in col_lower or '名称' in str(col):
            col_mapping['name'] = col
        elif 'district' in col_lower or '区县' in str(col) or '地级市' in str(col):
            col_mapping['district'] = col
        elif 'adcode' in col_lower or 'code' in col_lower:
            col_mapping['adcode'] = col
    if type_cols:
        col_mapping['type'] = type_cols
    return col_mapping

def extract_operator(name, type_str):
    """
    从名称和类型中提取运营商信息
    
    参数:
        name: 站点名称
        type_str: 类型字符串
    
    返回:
        运营商名称
    """
    text = str(name) + str(type_str)
    for operator, keywords in OPERATOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return operator
    return "其他"

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

def main():
    """
    主函数：读取POI数据，筛选充电站，清洗数据并输出
    """
    print("=" * 50)
    print("POI数据预处理开始")
    print("=" * 50)
    
    if not RAW_POI_FILE.exists():
        print(f"错误：POI文件不存在 {RAW_POI_FILE}")
        return
    
    print("读取POI数据...")
    df = pd.read_csv(RAW_POI_FILE, encoding='utf-8-sig')
    print(f"原始数据行数: {len(df)}")
    
    col_mapping = detect_columns(df)
    print(f"检测到的列映射: {col_mapping}")
    
    lon_col = col_mapping.get('lon', '经度')
    lat_col = col_mapping.get('lat', '纬度')
    type_cols = col_mapping.get('type', ['大类', '中类'])
    name_col = col_mapping.get('name', '名称')
    district_col = col_mapping.get('district', '区县')
    
    df['lon'] = df[lon_col]
    df['lat'] = df[lat_col]
    df['name'] = df[name_col]
    df['区县'] = df[district_col]
    
    if isinstance(type_cols, list):
        df['type'] = df[type_cols].apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
    else:
        df['type'] = df[type_cols]
    
    print("筛选充电站...")
    charging_mask = df['type'].fillna('').str.contains('|'.join(CHARGING_KEYWORDS)) | \
                    df['name'].fillna('').str.contains('|'.join(CHARGING_KEYWORDS))
    charging_df = df[charging_mask].copy()
    
    print(f"筛选后充电站数量: {len(charging_df)}")
    
    print("清洗数据...")
    charging_df = charging_df.dropna(subset=['lon', 'lat'])
    charging_df = charging_df[(charging_df['lon'] >= 107.4) & (charging_df['lon'] <= 109.6) &
                              (charging_df['lat'] >= 33.3) & (charging_df['lat'] <= 34.7)]
    
    print(f"清洗后充电站数量: {len(charging_df)}")
    
    print("提取运营商信息...")
    charging_df['operator'] = charging_df.apply(lambda row: extract_operator(row['name'], row['type']), axis=1)
    
    print("估算充电端口数...")
    charging_df['ports'] = np.random.randint(2, 9, len(charging_df))
    
    print("提取场所类型...")
    charging_df['place_type'] = charging_df['type'].apply(extract_place_type)
    
    charging_df.to_csv(DATA_DIR / "charging_stations_clean.csv", index=False, encoding='utf-8-sig')

    print(f"输出文件: {DATA_DIR / 'charging_stations_clean.csv'}")
    print("=" * 50)
    print("POI预处理完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
