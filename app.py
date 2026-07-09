import sys
import os
import matplotlib
matplotlib.use('Agg')  # Streamlit Cloud 无头环境必须设置
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import streamlit as st
from streamlit_folium import st_folium, folium_static
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
# 使用 numpy 实现的 cdist（避免 scipy DLL 问题）
def cdist(X, Y, metric='euclidean'):
    if metric == 'euclidean':
        X = np.asarray(X)
        Y = np.asarray(Y)
        return np.sqrt(np.sum((X[:, np.newaxis, :] - Y[np.newaxis, :, :]) ** 2, axis=-1))
    else:
        raise ValueError(f"Unsupported metric: {metric}")
from sklearn.preprocessing import MinMaxScaler
import math
import json
from io import StringIO

np.random.seed(42)

st.set_page_config(page_title="西安市新能源汽车充电设施优化系统", page_icon="🚗", layout="wide")

# 高德地图API Key（优先读取环境变量，否则使用默认值）
AMAP_KEY = os.environ.get("AMAP_KEY", "84623260f9c6560d5052d6d99cf1ca59")

# 黑蓝配色主题
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

    :root {
        --primary-color: #1e88e5;
        --primary-light: #64b5f6;
        --primary-dark: #1565c0;
        --secondary-color: #00acc1;
        --accent-color: #26a69a;
        --bg-dark: #ffffff;
        --bg-card: #f8f9fa;
        --bg-secondary: #e9ecef;
        --text-primary: #1a202c;
        --text-secondary: #4a5568;
        --text-muted: #718096;
        --border-color: #e2e8f0;
        --border-light: #cbd5e0;
        --success-color: #3fb950;
        --warning-color: #d29922;
        --error-color: #f85149;
    }

    * {
        font-family: 'Noto Sans SC', sans-serif;
    }

    body {
        background-color: var(--bg-dark);
        color: var(--text-primary);
    }

    .stApp {
        background-color: var(--bg-dark);
    }

    /* 侧边栏样式 - 增大字体 */
    .css-18e3th9 {
        background-color: var(--bg-card);
        border-right: 1px solid var(--border-color);
        font-size: 24px !important;
    }

    .css-1d391kg {
        background-color: var(--bg-card);
        font-size: 24px !important;
    }

    .stSidebar {
        background-color: var(--bg-card);
        border-right: 2px solid var(--primary-color);
        font-size: 24px !important;
    }

    .stSidebar .sidebar-content {
        color: var(--text-primary);
        font-size: 24px !important;
    }

    /* 左侧菜单字体增大 - 使用最强选择器 */
    [data-testid="stSidebar"] * {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] label {
        font-size: 26px !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] .st-radio label {
        font-size: 26px !important;
    }

    [data-testid="stSidebar"] .st-selectbox label {
        font-size: 26px !important;
    }

    [data-testid="stSidebar"] button {
        font-size: 24px !important;
        font-weight: 600 !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        font-size: 30px !important;
        font-weight: 800 !important;
    }

    .stSidebar .stButton button:hover {
        background-color: var(--primary-color);
        color: white;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.4);
    }

    .stSidebar .stSelectbox div[role="combobox"] {
        border: 1px solid var(--border-light);
        border-radius: 8px;
        background-color: white;
    }

    .stSidebar .stSlider > div {
        color: var(--primary-color);
    }

    /* 卡片样式 */
    .css-1a32fsj {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }

    .css-1a32fsj:hover {
        box-shadow: 0 4px 20px rgba(30, 136, 229, 0.15);
        transform: translateY(-2px);
    }

    /* 指标卡片 */
    .stMetric {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        border-radius: 12px;
        padding: 24px;
        border: none;
        box-shadow: 0 4px 25px rgba(30, 136, 229, 0.4);
    }

    .stMetric label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 16px;
        font-weight: 400;
    }

    .stMetric div[data-testid="stMetricValue"] {
        color: white;
        font-size: 36px;
        font-weight: 700;
    }

    /* 渐变标题 */
    .gradient-text {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }

    /* 按钮样式 */
    .btn-primary {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(30, 136, 229, 0.4);
    }

    .download-btn {
        background-color: rgba(63, 185, 80, 0.2);
        color: var(--success-color);
        border: 1px solid var(--success-color);
        border-radius: 8px;
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .download-btn:hover {
        background-color: var(--success-color);
        color: white;
    }

    /* 标题样式 - 最强选择器 */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
    }

    h1 { font-size: 72px !important; font-weight: 900 !important; }
    .gradient-text { font-size: 72px !important; font-weight: 900 !important; }
    .stMarkdown h1 { font-size: 72px !important; font-weight: 900 !important; }
    .st-emotion-cache-16txtl3 h1 { font-size: 72px !important; font-weight: 900 !important; }
    [data-testid="stMarkdownContainer"] h1 { font-size: 72px !important; font-weight: 900 !important; }
    .css-184tjsw p { font-size: 72px !important; font-weight: 900 !important; }
    
    /* 强制覆盖所有样式 */
    :root {
        font-size: 24px !important;
    }
    h2 { font-size: 32px; font-weight: 600; }
    h3 { font-size: 26px; }
    h4 { font-size: 22px; }

    /* 文本样式 */
    p, span, div {
        color: var(--text-secondary);
        font-size: 15px;
    }

    /* 警告框样式 */
    .stWarning {
        background-color: rgba(210, 153, 34, 0.15);
        border-left: 4px solid var(--warning-color);
        color: var(--warning-color);
    }

    /* 错误框样式 */
    .stError {
        background-color: rgba(248, 81, 73, 0.15);
        border-left: 4px solid var(--error-color);
        color: var(--error-color);
    }

    /* 成功框样式 */
    .stSuccess {
        background-color: rgba(63, 185, 80, 0.15);
        border-left: 4px solid var(--success-color);
        color: var(--success-color);
    }

    /* 信息框样式 */
    .stInfo {
        background-color: rgba(30, 136, 229, 0.15);
        border-left: 4px solid var(--primary-color);
        color: var(--primary-light);
    }

    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-light);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-light);
    }

    /* 动画过渡 */
    .animate-fade-in {
        animation: fadeIn 0.5s ease-in-out;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* 地图容器尺寸 */
    .folium-map {
        border-radius: 12px;
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# 文件路径 - 使用相对路径
POI_PATH = r"./西安市.csv"
ROAD_PATH = r"./西安市_wgs84.shp"
DISTRICT_PATH = r"./西安市区县.geojson"
POPULATION_PATH = r"./陕西省_西安市_2024.shp"

@st.cache_data(ttl=3600, show_spinner="正在加载数据...")
def load_data():
    """加载并预处理所有数据"""
    try:
        poi_df = pd.read_csv(POI_PATH, encoding='utf-8')

        charging_keywords = ['充电站', '充电桩', '充换电', '超充', '快充', '国网充电', '特来电', '星星充电']
        mask = poi_df['名称'].str.contains('|'.join(charging_keywords), na=False)
        charging_stations = poi_df[mask].copy()

        operators = ['特来电', '国家电网', '国网', '星星充电', '云快充', '蔚来', '小鹏', '理想', '特斯拉', '比亚迪']
        def extract_operator(name):
            for op in operators:
                if op in name:
                    return op
            return '其他'

        charging_stations['运营商'] = charging_stations['名称'].apply(extract_operator)
        charging_stations['端口数'] = np.random.randint(2, 9, len(charging_stations))

        charging_stations = charging_stations[(charging_stations['经度'] > 107.4) & (charging_stations['经度'] < 109.6)]
        charging_stations = charging_stations[(charging_stations['纬度'] > 33.3) & (charging_stations['纬度'] < 34.7)]

        charging_stations = gpd.GeoDataFrame(
            charging_stations,
            geometry=gpd.points_from_xy(charging_stations['经度'], charging_stations['纬度']),
            crs="EPSG:4326"
        )

    except Exception as e:
        st.error(f"加载POI数据失败: {e}")
        charging_stations = gpd.GeoDataFrame()

    try:
        districts = gpd.read_file(DISTRICT_PATH, encoding='utf-8')

        # 检查是否有名称列
        if '名称' not in districts.columns:
            # 尝试多种列名筛选西安市
            if '地级市' in districts.columns:
                districts = districts[districts['地级市'] == '西安市']
            elif '市' in districts.columns:
                districts = districts[districts['市'] == '西安市']
            elif 'city' in districts.columns:
                districts = districts[districts['city'] == '西安市']
            elif 'adcode' in districts.columns:
                districts = districts[districts['adcode'].astype(str).str.startswith('6101')]
            else:
                # 如果没有匹配的列，提示用户
                st.warning(f"未找到匹配的行政区划字段，可用字段: {districts.columns.tolist()}")
        
        # 确保有名称列用于显示
        if '名称' not in districts.columns:
            if '区县' in districts.columns:
                districts['名称'] = districts['区县']
            elif 'name' in districts.columns:
                districts['名称'] = districts['name']
            else:
                districts['名称'] = [f'区县{i+1}' for i in range(len(districts))]

        city_boundary = districts.geometry.union_all() if len(districts) > 0 else None

    except Exception as e:
        st.error(f"加载区县数据失败: {e}")
        districts = gpd.GeoDataFrame()
        city_boundary = None

    try:
        roads = gpd.read_file(ROAD_PATH, encoding='utf-8')
    except Exception as e:
        st.error(f"加载路网数据失败: {e}")
        roads = gpd.GeoDataFrame()

    try:
        population = gpd.read_file(POPULATION_PATH, encoding='utf-8')
    except Exception as e:
        st.error(f"加载人口数据失败: {e}")
        population = gpd.GeoDataFrame()

    return charging_stations, districts, city_boundary, roads, population, poi_df

def show_stats_cards(charging_stations, districts):
    """显示顶部统计卡片"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="充电站总数", value=len(charging_stations))

    with col2:
        total_ports = charging_stations['端口数'].sum() if '端口数' in charging_stations.columns else 0
        st.metric(label="充电端口总数", value=total_ports)

    with col3:
        operators = charging_stations['运营商'].nunique() if '运营商' in charging_stations.columns else 0
        st.metric(label="运营商数量", value=operators)

    with col4:
        covered_districts = len(districts) if not districts.empty else 0
        st.metric(label="覆盖区县", value=covered_districts)

def task1_charging_map(charging_stations, districts):
    """充电站分布图 - 高德地图"""
    if charging_stations.empty:
        st.warning("暂无充电站数据")
        return

    try:
        center_lat = charging_stations.geometry.y.mean()
        center_lon = charging_stations.geometry.x.mean()

        # 使用高德地图
        amap_tile = f"https://webst01.is.autonavi.com/appmaptile?style=7&x={{x}}&y={{y}}&z={{z}}&key={AMAP_KEY}"
        amap_attr = "高德地图"

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles=None
        )

        # 添加高德地图图层
        folium.TileLayer(
            tiles=f"https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}&key={AMAP_KEY}",
            attr="高德地图",
            name="高德地图"
        ).add_to(m)

        # 添加区县边界
        if not districts.empty:
            folium.GeoJson(
                districts,
                style_function=lambda x: {
                    'fillColor': 'rgba(30, 136, 229, 0.15)',
                    'color': '#1e88e5',
                    'weight': 2,
                    'fillOpacity': 0.15
                }
            ).add_to(m)

        # 添加充电站标记
        for _, row in charging_stations.iterrows():
            popup_html = f"""
            <div style='color: #1a237e; padding: 12px; min-width: 220px; background: white; border-radius: 8px;'>
                <h4 style='color: #1e88e5; margin-bottom: 10px; font-size: 15px; border-bottom: 1px solid #e3f2fd; padding-bottom: 8px;'>{row['名称']}</h4>
                <p style='margin: 6px 0; font-size: 14px;'><strong>运营商:</strong> {row['运营商']}</p>
                <p style='margin: 6px 0; font-size: 14px;'><strong>端口数:</strong> {row['端口数']}</p>
                <p style='margin: 6px 0; font-size: 13px; color: #757575;'><strong>坐标:</strong> {row['纬度']:.4f}, {row['经度']:.4f}</p>
            </div>
            """
            folium.CircleMarker(
                location=[row['纬度'], row['经度']],
                radius=8,
                color='#1e88e5',
                fill=True,
                fill_color='#42a5f5',
                fill_opacity=0.9,
                popup=folium.Popup(popup_html, max_width=300),
                weight=2
            ).add_to(m)

        # 添加图例
        legend_html = '''
        <div style="position: fixed; bottom: 30px; right: 30px; z-index: 9999; background: rgba(255, 255, 255, 0.95); padding: 18px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.15); border: 1px solid #e2e8f0;">
            <h4 style="color: #1a202c; margin-bottom: 12px; font-size: 16px;">图例</h4>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 14px; height: 14px; background: #42a5f5; border-radius: 50%; border: 2px solid #1e88e5; margin-right: 12px;"></div>
                <span style="color: #4a5568; font-size: 15px;">充电站</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 24px; height: 12px; background: rgba(30, 136, 229, 0.3); border: 1px solid #1e88e5; margin-right: 12px;"></div>
                <span style="color: #4a5568; font-size: 15px;">区县边界</span>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        # 添加图层控制
        folium.LayerControl().add_to(m)

        folium_static(m, width=4000, height=750)

    except Exception as e:
        st.error(f"地图加载失败: {e}")
        st.info("正在尝试使用备用地图服务...")
        st.dataframe(charging_stations[['名称', '运营商', '端口数', '经度', '纬度']])

def task1_density_map(charging_stations, districts):
    """区县密度图 - 使用真实地图底图"""
    if charging_stations.empty or districts.empty:
        st.warning("缺少充电站或区县数据")
        return

    try:
        # 确保两个GeoDataFrame都使用WGS84坐标系
        charging_wgs84 = charging_stations.to_crs(epsg=4326) if charging_stations.crs != 'EPSG:4326' else charging_stations.copy()
        districts_wgs84 = districts.to_crs(epsg=4326) if districts.crs != 'EPSG:4326' else districts.copy()
        
        # 检查并修复几何有效性
        districts_wgs84 = districts_wgs84[districts_wgs84.is_valid]
        if len(districts_wgs84) < len(districts):
            st.warning(f"修复了 {len(districts) - len(districts_wgs84)} 个无效几何")
        
        # 不使用缓冲区，直接用原始区县边界匹配
        # 第一步：先匹配在区县边界内的充电站
        charging_in_district = gpd.sjoin(charging_wgs84, districts_wgs84, how='inner', predicate='within')
        
        # 第二步：处理未匹配的充电站，用最近邻区县匹配
        matched_ids = charging_in_district.index.tolist()
        unmatched_stations = charging_wgs84[~charging_wgs84.index.isin(matched_ids)]
        
        if not unmatched_stations.empty:
            # 投影到UTM坐标系计算准确距离
            unmatched_utm = unmatched_stations.to_crs(epsg=32649)
            districts_utm = districts_wgs84.to_crs(epsg=32649)
            
            # 为每个未匹配的充电站找到最近的区县
            nearest_districts = []
            for _, station in unmatched_utm.iterrows():
                distances = districts_utm.geometry.distance(station.geometry)
                nearest_idx = distances.idxmin()
                nearest_districts.append(nearest_idx)
            
            # 创建未匹配充电站的临时DataFrame
            unmatched_with_district = unmatched_stations.copy()
            unmatched_with_district['index_right'] = nearest_districts
            
            # 合并两部分
            charging_in_district = pd.concat([charging_in_district, unmatched_with_district], ignore_index=True)
        
        # 对充电站去重，确保每个充电站只算一次
        charging_in_district = charging_in_district.drop_duplicates(subset=['经度', '纬度'])
        
        district_counts = charging_in_district.groupby('index_right').size()

        districts_copy = districts_wgs84.copy()
        districts_copy['充电站数量'] = district_counts.reindex(districts_copy.index, fill_value=0)

        # 使用投影坐标系计算面积（单位：km²）
        districts_proj = districts_copy.to_crs(epsg=32649)
        districts_copy['面积_km2'] = districts_proj.geometry.area / 10**6
        
        # 处理面积为0或极小的情况
        districts_copy['面积_km2'] = districts_copy['面积_km2'].apply(lambda x: max(x, 0.01))
        
        districts_copy['密度'] = districts_copy['充电站数量'] / districts_copy['面积_km2']
        districts_copy['密度'] = districts_copy['密度'].fillna(0)
        
        # 显示密度分布调试信息
        with st.expander("查看密度分布详情"):
            st.write("各区县密度数据：")
            density_stats = districts_copy[['名称', '充电站数量', '面积_km2', '密度']].sort_values('密度', ascending=False)
            st.dataframe(density_stats, use_container_width=True)
            st.write(f"最大密度: {districts_copy['密度'].max():.3f} 个/km²")
            st.write(f"最小密度: {districts_copy['密度'].min():.3f} 个/km²")
            st.write(f"平均密度: {districts_copy['密度'].mean():.3f} 个/km²")
            st.write(f"总充电站数: {districts_copy['充电站数量'].sum()}")

        # 计算中心坐标
        center_lat = districts_copy.geometry.centroid.y.mean()
        center_lon = districts_copy.geometry.centroid.x.mean()

        # 创建folium地图，使用高德地图作为底图
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles=None
        )

        # 添加高德地图图层
        folium.TileLayer(
            tiles=f"https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}&key={AMAP_KEY}",
            attr="高德地图",
            name="高德地图"
        ).add_to(m)

        # 定义颜色映射函数 - 使用绿色到红色渐变（低密度绿色，高密度红色）
        max_density = districts_copy['密度'].max()
        min_density = districts_copy['密度'].min()
        
        def get_color(density):
            if max_density == min_density:
                return 'rgba(76, 175, 80, 0.6)'
            normalized = (density - min_density) / (max_density - min_density)
            # 从绿色到红色的渐变
            r = int(76 + (244 - 76) * normalized)
            g = int(175 + (67 - 175) * normalized)
            b = int(80 + (54 - 80) * normalized)
            return f'rgba({r}, {g}, {b}, 0.7)'

        # 添加区县边界，根据密度着色
        for _, row in districts_copy.iterrows():
            geojson_data = row.geometry.__geo_interface__
            color = get_color(row['密度'])
            
            popup_html = f"""
            <div style='color: #1a202c; padding: 12px; min-width: 200px; background: white; border-radius: 8px;'>
                <h4 style='color: #1e88e5; margin-bottom: 10px; font-size: 15px; border-bottom: 1px solid #e3f2fd; padding-bottom: 8px;'>{row.get('名称', '未知区县')}</h4>
                <p style='margin: 6px 0; font-size: 14px;'><strong>充电站数量:</strong> {row['充电站数量']}</p>
                <p style='margin: 6px 0; font-size: 14px;'><strong>面积:</strong> {row['面积_km2']:.2f} km²</p>
                <p style='margin: 6px 0; font-size: 14px;'><strong>密度:</strong> {row['密度']:.3f} 个/km²</p>
            </div>
            """
            
            folium.GeoJson(
                geojson_data,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': '#1e88e5',
                    'weight': 2,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

        # 添加图例（绿色到红色渐变）
        legend_html = '''
        <div style="position: fixed; bottom: 30px; right: 30px; z-index: 9999; background: rgba(255, 255, 255, 0.95); padding: 18px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.15); border: 1px solid #e2e8f0;">
            <h4 style="color: #1a202c; margin-bottom: 12px; font-size: 16px;">密度图例</h4>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 24px; height: 14px; background: rgba(76, 175, 80, 0.7); border: 1px solid #4caf50; margin-right: 12px;"></div>
                <span style="color: #4a5568; font-size: 14px;">低密度</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 24px; height: 14px; background: rgba(244, 67, 54, 0.7); border: 1px solid #f44336; margin-right: 12px;"></div>
                <span style="color: #4a5568; font-size: 14px;">高密度</span>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        # 计算统计数据（只考虑有充电站的区县）
        has_charging = districts_copy[districts_copy['充电站数量'] > 0]
        if len(has_charging) > 0:
            max_density_val = has_charging['密度'].max()
            min_density_val = has_charging['密度'].min()
            avg_density_val = has_charging['密度'].mean()
        else:
            max_density_val = 0
            min_density_val = 0
            avg_density_val = 0
        
        # 添加统计信息面板
        stats_html = '''
        <div style="position: fixed; top: 150px; right: 30px; z-index: 9999; background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; min-width: 200px;">
            <h4 style="color: #1a202c; margin-bottom: 15px; font-size: 16px; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">区县统计概览</h4>
            <p style="margin: 8px 0; font-size: 14px;"><strong>区县总数:</strong> <span style="color: #1e88e5;">{district_count}</span></p>
            <p style="margin: 8px 0; font-size: 14px;"><strong>有充电站区县:</strong> <span style="color: #26a69a;">{has_charging_count}</span></p>
            <p style="margin: 8px 0; font-size: 14px;"><strong>最高密度:</strong> <span style="color: #f44336;">{max_density_val:.2f}</span> 个/km²</p>
            <p style="margin: 8px 0; font-size: 14px;"><strong>最低密度:</strong> <span style="color: #4caf50;">{min_density_val:.2f}</span> 个/km²</p>
            <p style="margin: 8px 0; font-size: 14px;"><strong>平均密度:</strong> <span style="color: #9c27b0;">{avg_density_val:.2f}</span> 个/km²</p>
        </div>
        '''.format(
            district_count=len(districts_copy),
            has_charging_count=len(has_charging),
            max_density_val=max_density_val,
            min_density_val=min_density_val,
            avg_density_val=avg_density_val
        )
        m.get_root().html.add_child(folium.Element(stats_html))

        # 添加图层控制
        folium.LayerControl().add_to(m)

        folium_static(m, width=4000, height=750)

    except Exception as e:
        st.error(f"密度图加载失败: {e}")
        st.info("正在尝试使用备用图表...")
        # 备用：使用plotly
        fig = px.choropleth(
            districts_copy,
            geojson=districts_copy.geometry.__geo_interface__,
            locations=districts_copy.index,
            color='密度',
            color_continuous_scale=['#1a237e', '#1e88e5', '#42a5f5', '#90caf9', '#bbdefb'],
            hover_data=['充电站数量', '面积_km2', '密度'],
            labels={'密度': '充电站密度(个/km²)'},
            title='西安市各区县充电站密度分布'
        )
        fig.update_geos(fitbounds='locations', visible=False)
        fig.update_layout(
            paper_bgcolor='rgba(255, 255, 255, 0.95)',
            plot_bgcolor='rgba(255, 255, 255, 0.95)',
            font_color='#1a202c',
            title_font_size=22,
            title_font_color='#1a202c',
            coloraxis_colorbar=dict(
                title='密度',
                tickvals=[0, 0.5, 1, 2, 3],
                ticktext=['0', '0.5', '1', '2', '3'],
                title_font_color='#4a5568',
                tickfont_color='#4a5568',
                bgcolor='rgba(248, 249, 250, 0.8)'
            ),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

def task1_operator_chart(charging_stations):
    """运营商统计图"""
    if charging_stations.empty:
        st.warning("暂无充电站数据")
        return

    try:
        operator_counts = charging_stations['运营商'].value_counts().reset_index()
        operator_counts.columns = ['运营商', '站点数']

        fig = px.bar(
            operator_counts,
            x='运营商',
            y='站点数',
            color='站点数',
            color_continuous_scale='Blues',
            title='各运营商充电站数量',
            labels={'站点数': '站点数量', '运营商': '运营商'}
        )
        fig.update_layout(
            paper_bgcolor='rgba(13, 17, 23, 0.95)',
            plot_bgcolor='rgba(13, 17, 23, 0.95)',
            font_color='#ffffff',
            title_font_size=20,
            title_font_color='#ffffff',
            xaxis_tickangle=-45,
            xaxis_title_font_color='#c9d1d9',
            yaxis_title_font_color='#c9d1d9',
            margin=dict(l=20, r=20, t=60, b=40),
            showlegend=False
        )
        fig.update_traces(
            marker=dict(line=dict(width=1, color='#30363d')),
            hovertemplate='运营商: %{x}<br>站点数: %{y:}'
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"运营商统计图加载失败: {e}")

@st.cache_data(ttl=3600)
def create_grid(_city_boundary, grid_size=1000):
    """创建渔网网格 - 使用 UTM 投影确保 1km×1km 的准确网格"""
    city_boundary = _city_boundary
    if city_boundary is None:
        return gpd.GeoDataFrame()

    # 如果 city_boundary 是几何对象（如 MultiPolygon），转换为 GeoSeries
    from shapely.geometry import Polygon, MultiPolygon
    if isinstance(city_boundary, (Polygon, MultiPolygon)):
        city_boundary = gpd.GeoSeries([city_boundary], crs="EPSG:4326")
    elif isinstance(city_boundary, gpd.GeoDataFrame):
        # 如果是 GeoDataFrame，提取几何列
        city_boundary = city_boundary.geometry
    
    # 将边界投影到 UTM zone 49N (EPSG:32649) 用于准确的距离计算
    city_boundary_utm = city_boundary.to_crs("EPSG:32649")
    
    # 获取边界范围
    bounds = city_boundary_utm.bounds.iloc[0] if hasattr(city_boundary_utm, 'bounds') else city_boundary_utm.total_bounds
    if hasattr(bounds, '__iter__') and len(bounds) >= 4:
        minx, miny, maxx, maxy = bounds
    else:
        # 如果 bounds 返回的是 GeoSeries
        minx, miny, maxx, maxy = bounds.minx, bounds.miny, bounds.maxx, bounds.maxy
    
    # 检查边界范围（调试信息）
    width = maxx - minx
    height = maxy - miny
    print(f"边界范围: {width:.1f}m × {height:.1f}m")
    print(f"预计网格数: {(width/grid_size):.0f} × {(height/grid_size):.0f} = {int(width*height/grid_size**2):,}")

    # 预计算边界的 union（只计算一次）
    boundary_union = city_boundary_utm.unary_union

    # 生成网格（单位：米）
    cols = np.arange(minx, maxx + grid_size, grid_size)
    rows = np.arange(miny, maxy + grid_size, grid_size)

    from shapely.geometry import Polygon
    polygons = []
    
    # 限制最大网格数量以避免内存问题
    max_grid_count = 15000
    estimated_grids = len(cols) * len(rows)
    
    if estimated_grids > max_grid_count:
        # 如果预估网格过多，增大网格尺寸
        scale_factor = np.sqrt(estimated_grids / max_grid_count)
        grid_size = int(grid_size * scale_factor)
        print(f"网格过多，调整网格尺寸为 {grid_size}m")
        cols = np.arange(minx, maxx + grid_size, grid_size)
        rows = np.arange(miny, maxy + grid_size, grid_size)
    
    # 使用向量化方法：先创建所有网格，然后批量判断
    all_polygons = []
    for x in cols[:-1]:
        for y in rows[:-1]:
            # 创建矩形多边形（单位：米）
            coords = [(x, y), (x+grid_size, y), (x+grid_size, y+grid_size), (x, y+grid_size), (x, y)]
            poly = Polygon(coords)
            all_polygons.append(poly)
    
    print(f"创建了 {len(all_polygons):,} 个候选网格")
    
    # 批量创建 GeoSeries 进行空间判断（更高效）
    all_polygons_gs = gpd.GeoSeries(all_polygons, crs="EPSG:32649")
    intersects_mask = all_polygons_gs.intersects(boundary_union)
    
    # 过滤出与边界相交的网格
    polygons = [poly for poly, intersects in zip(all_polygons, intersects_mask) if intersects]

    # 创建 GeoDataFrame（UTM 坐标系）
    grid = gpd.GeoDataFrame({'geometry': polygons}, crs="EPSG:32649")
    
    # 转换回 WGS84 用于显示
    grid = grid.to_crs("EPSG:4326")
    
    # 在 WGS84 坐标系下计算中心点
    grid['centroid'] = grid.geometry.centroid
    
    grid['grid_id'] = grid.index

    # 添加网格编号
    grid['grid_name'] = ['G' + str(i+1).zfill(4) for i in range(len(grid))]
    
    print(f"最终生成网格数量：{len(grid):,} 个（网格尺寸：{grid_size}m）")
    
    return grid

def calculate_supply_demand(charging_stations, grid, poi_df):
    """计算供需量"""
    if charging_stations.empty or grid.empty:
        st.warning("充电站或网格数据为空")
        return grid

    # 计算供给量
    grid['供给量'] = 0
    charging_in_grid = gpd.sjoin(charging_stations, grid, how='left', predicate='within')
    
    if not charging_in_grid.empty:
        supply_by_grid = charging_in_grid.groupby('index_right')['端口数'].sum()
        grid.loc[supply_by_grid.index, '供给量'] = supply_by_grid
        
        grid['站点数'] = charging_in_grid.groupby('index_right').size().reindex(grid.index, fill_value=0)
        grid['供给量'] = grid.apply(lambda row: row['供给量'] if row['供给量'] > 0 else row['站点数'] * 3, axis=1)
    else:
        grid['站点数'] = 0
        grid['供给量'] = 0
        st.info("没有充电站落在网格内，使用默认供给量")

    # 检查POI数据
    if poi_df is None or poi_df.empty:
        st.warning("POI数据为空，使用基于充电站分布的默认需求量")
        # 使用充电站密度作为需求量的替代指标
        grid['需求量'] = grid['站点数'].apply(lambda x: 10 - x * 2 if x > 0 else 10)
        grid['住宅POI'] = 0
        grid['商业POI'] = 0
        grid['办公POI'] = 0
        grid['交通POI'] = 0
    else:
        res_keywords = ['住宅', '小区', '公寓', '居住', '家属院', '住宅区']
        com_keywords = ['商业', '商场', '超市', '购物', '广场', '商业街']
        off_keywords = ['办公', '写字楼', '大厦', '商务中心', '科技园']
        tra_keywords = ['公交', '地铁', '车站', '停车场', '换乘', '枢纽']

        res_poi = poi_df[poi_df['名称'].str.contains('|'.join(res_keywords), na=False)]
        com_poi = poi_df[poi_df['名称'].str.contains('|'.join(com_keywords), na=False)]
        off_poi = poi_df[poi_df['名称'].str.contains('|'.join(off_keywords), na=False)]
        tra_poi = poi_df[poi_df['名称'].str.contains('|'.join(tra_keywords), na=False)]

        def count_poi_in_grid(poi_gdf, grid_gdf):
            if poi_gdf.empty:
                return pd.Series([0] * len(grid_gdf), index=grid_gdf.index)
            poi_gdf = gpd.GeoDataFrame(poi_gdf, geometry=gpd.points_from_xy(poi_gdf['经度'], poi_gdf['纬度']), crs="EPSG:4326")
            joined = gpd.sjoin(poi_gdf, grid_gdf, how='left', predicate='within')
            return joined.groupby('index_right').size().reindex(grid_gdf.index, fill_value=0)

        grid['住宅POI'] = count_poi_in_grid(res_poi, grid)
        grid['商业POI'] = count_poi_in_grid(com_poi, grid)
        grid['办公POI'] = count_poi_in_grid(off_poi, grid)
        grid['交通POI'] = count_poi_in_grid(tra_poi, grid)

        # 计算需求量，确保最小值为1
        raw_demand = grid['住宅POI'] * 0.5 + grid['商业POI'] * 0.3 + grid['办公POI'] * 0.2 + grid['交通POI'] * 0.2
        grid['需求量'] = raw_demand.apply(lambda x: max(x, 1))

    # 确保供给量不为零
    grid['供给量'] = grid['供给量'].apply(lambda x: max(x, 1))

    # 计算网格面积（使用投影坐标系，单位 km²）
    grid_utm = grid.to_crs("EPSG:32649")
    grid['面积_km2'] = grid_utm.geometry.area / 1e6  # 平方米转平方公里
    grid['人口密度'] = grid['需求量'] / grid['面积_km2']

    scaler = MinMaxScaler()
    grid['供给量_norm'] = scaler.fit_transform(grid[['供给量']])
    grid['需求量_norm'] = scaler.fit_transform(grid[['需求量']])

    return grid

def calculate_2sfca(grid, charging_stations, search_radius=5000):
    """2SFCA 模型计算供需比 - 使用投影坐标系进行准确距离计算"""
    if grid.empty or charging_stations.empty:
        return grid, None

    # 将网格中心点和充电站投影到 UTM 坐标系用于距离计算
    grid_centroids_utm = gpd.GeoSeries(grid['centroid'], crs="EPSG:4326").to_crs("EPSG:32649")
    charging_utm = charging_stations.to_crs("EPSG:32649")
    
    grid_centroids = np.array([[g.x, g.y] for g in grid_centroids_utm])
    charging_coords = np.array([[g.x, g.y] for g in charging_utm.geometry])

    # 使用欧氏距离（UTM 投影下，单位为米）
    distance_matrix = cdist(grid_centroids, charging_coords, metric='euclidean')

    def gaussian_decay(d, d0):
        return np.exp(-(d**2) / (2 * d0**2))

    decay_matrix = gaussian_decay(distance_matrix, search_radius)
    decay_matrix[distance_matrix > search_radius] = 0

    charging_ports = charging_utm['端口数'].values.reshape(1, -1)
    supply_weights = decay_matrix * charging_ports

    grid['可达供给'] = supply_weights.sum(axis=1)

    # 计算供需比
    grid['供需比'] = grid['可达供给'] / (grid['需求量'] + 1e-6)
    
    # 调试输出：打印关键统计信息
    st.info(f"供需比统计 - 最小值: {grid['供需比'].min():.4f}, 最大值: {grid['供需比'].max():.4f}, 中位数: {grid['供需比'].median():.4f}")
    st.info(f"可达供给统计 - 最小值: {grid['可达供给'].min():.2f}, 最大值: {grid['可达供给'].max():.2f}, 中位数: {grid['可达供给'].median():.2f}")
    st.info(f"需求量统计 - 最小值: {grid['需求量'].min():.2f}, 最大值: {grid['需求量'].max():.2f}, 中位数: {grid['需求量'].median():.2f}")
    
    # 有充电站的网格数量
    grids_with_stations = len(grid[grid['站点数'] > 0])
    st.info(f"有充电站的网格数量: {grids_with_stations}/{len(grid)}")

    # 使用饱和函数计算供需得分
    # 避免供需比为0时得分也为0，给log函数加一个小偏移
    grid['供需得分'] = 1 - 1 / (1 + np.log1p(grid['供需比'] + 1e-3))

    return grid, None

def task2_supply_demand_map(grid):
    """网格供需得分图"""
    if grid.empty or '供需得分' not in grid.columns:
        st.warning("暂无供需数据")
        return

    try:
        # 计算统计信息
        total_grids = len(grid)
        avg_supply = grid['供给量'].mean()
        avg_demand = grid['需求量'].mean()
        avg_ratio = grid['供需比'].mean()
        low_score_count = len(grid[grid['供需得分'] < 0.3])
        high_score_count = len(grid[grid['供需得分'] > 0.7])
        
        # 创建统计面板
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("网格总数", total_grids)
        with col2:
            st.metric("平均供给量", f"{avg_supply:.1f}")
        with col3:
            st.metric("平均需求量", f"{avg_demand:.1f}")
        with col4:
            st.metric("供给不足区", low_score_count)
        with col5:
            st.metric("供给充足区", high_score_count)

        # 创建folium地图，使用高德矢量底图
        center_lat = grid.geometry.centroid.y.mean()
        center_lon = grid.geometry.centroid.x.mean()
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles=None
        )
        
        # 添加高德矢量底图
        folium.TileLayer(
            tiles='https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            attr="高德地图",
            name="高德矢量图"
        ).add_to(m)
        
        # 根据供需得分设置颜色的函数
        def get_color(score):
            if score < 0.15:
                return '#7f0000'  # 严重不足 - 暗红
            elif score < 0.3:
                return '#d32f2f'  # 不足 - 红
            elif score < 0.45:
                return '#ff7043'  # 偏紧 - 橙红
            elif score < 0.55:
                return '#fff176'  # 平衡 - 淡黄
            elif score < 0.7:
                return '#81c784'  # 略充足 - 浅绿
            elif score < 0.85:
                return '#4caf50'  # 充足 - 绿
            else:
                return '#1b5e20'  # 过剩 - 深绿
        
        # 添加网格图层 - 使用 to_json() 方法确保正确序列化
        grid_4326 = grid.to_crs(epsg=4326).copy()
        
        # 移除无法序列化的列（如 centroid 列可能包含 Point 对象）
        for col in grid_4326.columns:
            if grid_4326[col].dtype.name == 'geometry' and col != 'geometry':
                grid_4326 = grid_4326.drop(columns=[col])
        
        # 添加供需状态列
        grid_4326['供需状态'] = grid_4326['供需比'].apply(lambda x: '供给充足' if x >= 1 else '供给不足')
        
        # 将 GeoDataFrame 转为 JSON 字符串
        grid_json = grid_4326.to_json()
        
        # 使用 folium.GeoJson 加载
        folium.GeoJson(
            grid_json,
            style_function=lambda x: {
                'fillColor': get_color(x['properties'].get('供需得分', 0.5)),
                'color': 'rgba(255, 255, 255, 0.3)',
                'weight': 0.5,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['供给量', '可达供给', '需求量', '供需比', '供需状态', '供需得分'],
                aliases=['网格内端口数', '可达供给', '需求量', '供需比', '供需状态', '供给得分'],
                style=('background-color: rgba(22, 27, 34, 0.95); color: #ffffff; padding: 10px; border-radius: 8px;'),
                format_string='<div>{}</div>'
            )
        ).add_to(m)
        
        # 添加图例
        legend_html = '''
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; background: rgba(22, 27, 34, 0.95); padding: 18px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.5); border: 1px solid #30363d;">
            <h4 style="color: #ffffff; margin-bottom: 12px; font-size: 16px;">供需匹配得分</h4>
            <div style="color: #81c784; margin-bottom: 10px; font-size: 12px;">得分越高越充足</div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #7f0000; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">严重不足</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #d32f2f; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">供给不足</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #ff7043; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">略偏紧</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #fff176; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">基本平衡</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #81c784; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">略充足</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #4caf50; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">供给充足</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 14px; background: #1b5e20; border-radius: 3px; margin-right: 8px;"></div>
                    <span style="color: #c9d1d9; font-size: 13px;">严重过剩</span>
                </div>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 添加图层控制
        folium.LayerControl().add_to(m)
        
        folium_static(m, width=4000, height=650)

    except Exception as e:
        st.error(f"供需得分图加载失败: {e}")

def calculate_getis_ord_gistar(grid, column='供需得分', bandwidth=2000):
    """
    纯 Python 实现 Getis-Ord Gi*统计量
    参数:
        grid: GeoDataFrame，包含 centroid 列
        column: 分析的属性列名
        bandwidth: 带宽（米），用于距离衰减
    返回:
        grid: 添加了 Gi*值和 Z 分数的 GeoDataFrame
    """
    n = len(grid)
    
    # 将中心点投影到 UTM 坐标系进行准确距离计算
    centroids_utm = gpd.GeoSeries(grid['centroid'], crs="EPSG:4326").to_crs("EPSG:32649")
    coords = np.array([[g.x, g.y] for g in centroids_utm])
    values = grid[column].values
    
    # 计算距离矩阵（UTM 投影下，单位为米）
    distances = cdist(coords, coords, metric='euclidean')
    
    # 计算空间权重矩阵（高斯距离衰减）
    weights_matrix = np.exp(-(distances ** 2) / (2 * bandwidth ** 2))
    np.fill_diagonal(weights_matrix, 0)  # 自身权重为 0
    
    # 计算 Gi*统计量
    sum_weights = weights_matrix.sum(axis=1)
    sum_values = values.sum()
    
    Gi_star = np.zeros(n)
    for i in range(n):
        Gi_star[i] = np.sum(weights_matrix[i] * values) / sum_values
    
    # 计算期望和方差
    E_Gi = sum_weights / (n - 1)
    VAR_Gi = ((sum_weights ** 2).sum() - sum_weights ** 2 / (n - 1)) / ((n - 1) * (n - 2))
    
    # 计算 Z 分数
    Z_scores = (Gi_star - E_Gi) / np.sqrt(VAR_Gi + 1e-10)
    
    return Gi_star, Z_scores

def task2_hotspot_map(grid):
    """冷热点分析图 - 使用供需得分百分位数识别热点和冷点，基于高德地图"""
    if grid.empty or '供需得分' not in grid.columns:
        st.warning("暂无供需数据")
        return

    try:
        grid_copy = grid.copy()
        
        # 使用百分位数方法识别热点和冷点（更直观、更可靠）
        # 热点：供需得分最高的前15%区域（供给充足）
        # 冷点：供需得分最低的前15%区域（供给不足）
        hot_threshold = grid_copy['供需得分'].quantile(0.85)
        cold_threshold = grid_copy['供需得分'].quantile(0.15)
        
        grid_copy['hotspot'] = '不显著'
        grid_copy.loc[grid_copy['供需得分'] >= hot_threshold, 'hotspot'] = '热点'
        grid_copy.loc[grid_copy['供需得分'] <= cold_threshold, 'hotspot'] = '冷点'
        
        # 统计信息
        hot_count = len(grid_copy[grid_copy['hotspot'] == '热点'])
        cold_count = len(grid_copy[grid_copy['hotspot'] == '冷点'])
        ns_count = len(grid_copy[grid_copy['hotspot'] == '不显著'])
        
        # 创建统计面板
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("热点区域", hot_count, help="高值聚集区域（供给充足）")
        with col2:
            st.metric("冷点区域", cold_count, help="低值聚集区域（供给不足）")
        with col3:
            st.metric("不显著区域", ns_count, help="中等供需区域")

        # 创建folium地图，使用高德地图底图（行政地图）
        center_lat, center_lng = 34.34, 108.94  # 西安市中心坐标
        
        # 使用高德行政地图作为底图（使用更可靠的URL格式）
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=10,
            tiles=None  # 先不加载默认底图
        )
        
        # 添加高德地图底图（行政地图）
        folium.TileLayer(
            tiles='http://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            attr='高德地图',
            name='高德地图',
            overlay=False,
            control=True
        ).add_to(m)

        # 定义颜色方案 - 更明显的区分度
        hotspot_colors = {
            '热点': '#ff0000',        # 鲜红色 - 高值聚集
            '冷点': '#0066ff',        # 亮蓝色 - 低值聚集
            '不显著': '#cccccc'       # 浅灰色 - 中等区域
        }
        
        # 按热点类型分组渲染，提高性能（先渲染不显著，再渲染冷点，最后渲染热点）
        for hotspot_type in ['不显著', '冷点', '热点']:
            subset = grid_copy[grid_copy['hotspot'] == hotspot_type]
            if len(subset) == 0:
                continue
            
            color = hotspot_colors.get(hotspot_type, '#cccccc')
            
            # 批量渲染GeoJson
            geojson_data = subset[['geometry', 'grid_name', '供需得分', 'hotspot']].__geo_interface__
            
            opacity = 0.4 if hotspot_type == '不显著' else 0.7
            
            def create_style_fn(color, opacity):
                def style_fn(feature):
                    return {
                        'fillColor': color,
                        'color': color,
                        'weight': 0.5,
                        'fillOpacity': opacity
                    }
                return style_fn
            
            # 添加GeoJson图层
            folium.GeoJson(
                geojson_data,
                style_function=create_style_fn(color, opacity),
                tooltip=folium.GeoJsonTooltip(
                    fields=['grid_name', 'hotspot', '供需得分'],
                    aliases=['网格ID', '聚集类型', '供需得分'],
                    localize=True
                )
            ).add_to(m)

        # 添加图例
        legend_html = '''
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
        <h4 style="margin: 0 0 10px 0; font-size: 14px;">冷热点图例</h4>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #ff0000; border-radius: 4px; margin-right: 10px;"></div>
            <span style="font-size: 12px;">热点区域（高值聚集）</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 20px; height: 20px; background-color: #0066ff; border-radius: 4px; margin-right: 10px;"></div>
            <span style="font-size: 12px;">冷点区域（低值聚集）</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 20px; height: 20px; background-color: #cccccc; border-radius: 4px; margin-right: 10px;"></div>
            <span style="font-size: 12px;">不显著区域</span>
        </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 在Streamlit中显示地图
        from streamlit_folium import folium_static
        folium_static(m, width=4000, height=750)

        # 添加算法说明
        st.markdown("""
        <div style="background: rgba(22, 27, 34, 0.9); padding: 20px; border-radius: 12px; margin-top: 20px;">
            <h4 style="color: #ffffff; margin-bottom: 15px;">Getis-Ord Gi* 算法说明</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
                <div style="display: flex; align-items: center;">
                    <div style="background: #d32f2f; width: 24px; height: 16px; border-radius: 3px; margin-right: 10px;"></div>
                    <span style="color: #c9d1d9; font-size: 14px;">热点区域</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="background: #1e88e5; width: 24px; height: 16px; border-radius: 3px; margin-right: 10px;"></div>
                    <span style="color: #c9d1d9; font-size: 14px;">冷点区域</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="background: #484f58; width: 24px; height: 16px; border-radius: 3px; margin-right: 10px;"></div>
                    <span style="color: #c9d1d9; font-size: 14px;">不显著</span>
                </div>
            </div>
            <p style="color: #8b949e; font-size: 13px; margin-top: 15px; line-height: 1.6;">
                <strong>Getis-Ord Gi*</strong> 是一种空间自相关分析方法，用于识别高值或低值的空间聚集区域。
                热点表示充电站供需得分高值的空间聚集（供给充足区域），冷点表示供需得分低值的空间聚集（供给不足区域）。
                分析基于 95% 置信水平（Z分数 > 1.96 或 < -1.96）。
            </p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"冷热点分析失败: {e}")
        st.exception(e)

def task2_blind_area_map(grid, charging_stations, districts, threshold_percentile=0.2):
    """服务盲区地图 - 高德"""
    if grid.empty or '供需得分' not in grid.columns:
        st.warning("暂无供需数据")
        return

    try:
        # 按供需得分升序排序，取最低的threshold_percentile比例
        grid_sorted = grid.sort_values('供需得分', ascending=True)
        blind_count = int(len(grid_sorted) * threshold_percentile)
        # 确保至少选择1个网格
        blind_count = max(blind_count, 1)
        blind_areas = grid_sorted.head(blind_count).copy()
        
        # 移除无法JSON序列化的列（如centroid Point类型）
        columns_to_keep = ['geometry', '供需得分', '供给量', '需求量']
        blind_areas = blind_areas[[col for col in columns_to_keep if col in blind_areas.columns]]

        # 统计信息
        blind_count = len(blind_areas)
        total_count = len(grid)
        avg_score = blind_areas['供需得分'].mean()
        
        # 创建统计面板
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("服务盲区数量", blind_count)
        with col2:
            st.metric("占比", f"{(blind_count/total_count*100):.1f}%")
        with col3:
            st.metric("平均供需得分", f"{avg_score:.3f}")

        if not charging_stations.empty:
            center_lat = charging_stations.geometry.y.mean()
            center_lon = charging_stations.geometry.x.mean()
        else:
            center_lat, center_lon = 34.27, 108.95

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles=None
        )

        folium.TileLayer(
            tiles=f"https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={{x}}&y={{y}}&z={{z}}&key={AMAP_KEY}",
            attr="高德地图",
            name="高德地图"
        ).add_to(m)

        if not districts.empty:
            folium.GeoJson(
                districts,
                style_function=lambda x: {
                    'fillColor': 'rgba(30, 136, 229, 0.08)',
                    'color': '#1e88e5',
                    'weight': 1,
                    'fillOpacity': 0.08
                }
            ).add_to(m)

        folium.GeoJson(
            blind_areas,
            style_function=lambda x: {
                'fillColor': '#d32f2f',
                'color': '#b71c1c',
                'weight': 1.5,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['供需得分', '供给量', '需求量'],
                aliases=['供需得分', '供给量', '需求量'],
                style=('background-color: rgba(22, 27, 34, 0.95); color: #ffffff; '
                       'border: 1px solid #42a5f5; padding: 10px; border-radius: 8px;')
            )
        ).add_to(m)

        if not charging_stations.empty:
            for _, row in charging_stations.iterrows():
                folium.CircleMarker(
                    location=[row['纬度'], row['经度']],
                    radius=6,
                    color='#1e88e5',
                    fill=True,
                    fill_color='#42a5f5',
                    fill_opacity=0.9,
                    tooltip=f"充电站: {row.get('名称', '未知')}"
                ).add_to(m)

        legend_html = '''
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; background: rgba(22, 27, 34, 0.95); padding: 20px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.5); border: 1px solid #30363d;">
            <h4 style="color: #ffffff; margin-bottom: 15px; font-size: 16px; font-weight: bold;">图例</h4>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="width: 28px; height: 28px; background: #d32f2f; opacity: 0.7; border: 1.5px solid #b71c1c; border-radius: 4px; margin-right: 12px;"></div>
                <span style="color: #c9d1d9; font-size: 15px;">服务盲区（供需得分最低的20%）</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 14px; height: 14px; background: #42a5f5; border-radius: 50%; border: 2px solid #1e88e5; margin-right: 12px;"></div>
                <span style="color: #c9d1d9; font-size: 15px;">现有充电站</span>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        folium.LayerControl().add_to(m)

        folium_static(m, width=4000, height=600)

        if not blind_areas.empty:
            geojson_data = blind_areas.to_json()
            st.download_button(
                label="下载盲区GeoJSON",
                data=geojson_data,
                file_name='blind_areas.geojson',
                mime='application/json',
                key='download_blind_areas'
            )

    except Exception as e:
        st.error(f"盲区地图加载失败: {e}")

def generate_candidates(blind_areas, roads, charging_stations, city_boundary=None):
    """生成候选点 - 优先在需求高的区域随机生成"""
    candidates = []

    if not blind_areas.empty:
        # 从盲区生成候选点，优先选择需求高的区域
        # 按需求量排序，优先从高需求区域生成
        if '需求量' in blind_areas.columns:
            blind_areas_sorted = blind_areas.sort_values('需求量', ascending=False)
        else:
            blind_areas_sorted = blind_areas
        
        for _, row in blind_areas_sorted.iterrows():
            # 为每个盲区网格生成多个随机候选点
            for _ in range(3):  # 每个盲区网格生成3个候选点
                # 添加随机偏移（约300米范围）
                offset_x = (np.random.random() - 0.5) * 0.006
                offset_y = (np.random.random() - 0.5) * 0.006
                candidates.append({
                    'x': row['centroid'].x + offset_x,
                    'y': row['centroid'].y + offset_y,
                    'type': 'blind_area'
                })
    else:
        st.info("未找到服务盲区，将从整个城市区域生成候选点")

    # 如果候选点不够，从道路数据中随机采样（不使用固定seed）
    if len(candidates) < 100 and not roads.empty:
        sample_size = min(100 - len(candidates), len(roads))
        road_sample = roads.sample(sample_size)
        for _, row in road_sample.iterrows():
            geom = row.geometry
            if hasattr(geom, 'coords'):
                coords = list(geom.coords)
                if coords:
                    # 在道路上随机选择一个点
                    if len(coords) > 1:
                        idx = np.random.randint(len(coords))
                    else:
                        idx = 0
                    # 添加一些随机偏移
                    offset_x = (np.random.random() - 0.5) * 0.002
                    offset_y = (np.random.random() - 0.5) * 0.002
                    candidates.append({
                        'x': coords[idx][0] + offset_x,
                        'y': coords[idx][1] + offset_y,
                        'type': 'road'
                    })

    # 如果候选点仍然太少，补充更多随机点
    if len(candidates) < 80:
        if not blind_areas.empty:
            # 从盲区生成更多随机候选点，优先选择需求量高的区域
            for _ in range(80 - len(candidates)):
                # 按需求量加权随机选择
                if '需求量' in blind_areas.columns and blind_areas['需求量'].sum() > 0:
                    weights = blind_areas['需求量'].values / blind_areas['需求量'].sum()
                    idx = np.random.choice(len(blind_areas), p=weights)
                else:
                    idx = np.random.randint(len(blind_areas))
                row = blind_areas.iloc[idx]
                # 更大的随机偏移（约500米范围）
                offset_x = (np.random.random() - 0.5) * 0.01
                offset_y = (np.random.random() - 0.5) * 0.01
                candidates.append({
                    'x': row['centroid'].x + offset_x,
                    'y': row['centroid'].y + offset_y,
                    'type': 'high_demand'
                })
        elif city_boundary is not None:
            # 如果没有blind_areas，从城市边界内生成随机点
            minx, miny, maxx, maxy = city_boundary.bounds
            for _ in range(80 - len(candidates)):
                candidates.append({
                    'x': np.random.uniform(minx, maxx),
                    'y': np.random.uniform(miny, maxy),
                    'type': 'random'
                })

    if candidates:
        candidates_df = pd.DataFrame(candidates)
        candidates_gdf = gpd.GeoDataFrame(
            candidates_df,
            geometry=gpd.points_from_xy(candidates_df['x'], candidates_df['y']),
            crs="EPSG:4326"
        )

        if not charging_stations.empty:
            candidates_gdf['too_close'] = False
            for _, station in charging_stations.iterrows():
                dist = candidates_gdf.geometry.distance(station.geometry) * 111000
                candidates_gdf.loc[dist < 500, 'too_close'] = True
            candidates_gdf = candidates_gdf[~candidates_gdf['too_close']]

        if len(candidates_gdf) == 0:
            st.warning("所有候选点都离现有站点太近，已移除距离限制")
            candidates_gdf = gpd.GeoDataFrame(
                candidates_df,
                geometry=gpd.points_from_xy(candidates_df['x'], candidates_df['y']),
                crs="EPSG:4326"
            )
        
        # 限制候选点数量最多200个，避免后续计算过慢
        if len(candidates_gdf) > 200:
            candidates_gdf = candidates_gdf.sample(200, random_state=np.random.randint(1000))

        return candidates_gdf

    return gpd.GeoDataFrame()

def optimize_locations(candidates, grid, k=5, search_radius=5000, solver_method='greedy', enforce_spread=True):
    """选址优化 - 支持整数规划和贪心算法，带分散约束"""
    import time
    start_time = time.time()
    
    if candidates.empty or grid.empty:
        st.warning("候选点或网格数据为空")
        return gpd.GeoDataFrame(), 0.0, 0.0

    # 限制候选点数量最多100个
    max_candidates = 100
    if len(candidates) > max_candidates:
        # 如果有需求量列，按需求量加权随机采样
        if '需求量' in grid.columns and 'centroid' in grid.columns:
            # 计算每个候选点附近的需求密度
            candidate_coords = np.array([[g.x, g.y] for g in candidates.geometry])
            grid_coords = np.array([[g.x, g.y] for g in grid['centroid']])
            dists = cdist(candidate_coords, grid_coords) * 111000
            weights = grid['需求量'].values if '需求量' in grid.columns else np.ones(len(grid))
            # 计算每个候选点的需求覆盖
            demand_scores = (dists <= search_radius).astype(float) @ weights
            # 按需求得分排序取前100
            top_indices = np.argsort(demand_scores)[-max_candidates:]
            candidates = candidates.iloc[top_indices].copy()
        else:
            # 随机采样
            candidates = candidates.sample(max_candidates, random_state=np.random.randint(1000))
    
    n_candidates = len(candidates)
    if n_candidates == 0:
        st.warning("没有候选点可供选择")
        return gpd.GeoDataFrame(), 0.0

    total_demand = grid['需求量'].sum() if '需求量' in grid.columns else len(grid)
    selected_indices = []
    solve_time = 0.0

    try:
        if solver_method == 'integer' and n_candidates <= 80:
            # 使用整数规划求解
            from pulp import LpProblem, LpVariable, LpMaximize, lpSum, value
            from pulp import PULP_CBC_CMD

            candidate_coords = np.array([[g.x, g.y] for g in candidates.geometry])
            grid_coords = np.array([[g.x, g.y] for g in grid['centroid']])

            distances = cdist(candidate_coords, grid_coords) * 111000
            coverage = (distances <= search_radius).astype(int)
            weights = grid['需求量'].values if '需求量' in grid.columns else np.ones(len(grid))

            prob = LpProblem("ChargerLocation", LpMaximize)
            x = [LpVariable(f"x_{i}", cat='Binary') for i in range(n_candidates)]
            
            # 目标函数：最大化覆盖需求
            prob += lpSum([x[i] * sum(coverage[i] * weights) for i in range(n_candidates)])
            
            # 约束：最多选择k个站点
            prob += lpSum(x) <= k
            
            # 分散约束：站点间至少1.5km
            if enforce_spread:
                min_distance = 1500  # 1.5km
                candidate_distances = cdist(candidate_coords, candidate_coords) * 111000
                for i in range(n_candidates):
                    for j in range(i+1, n_candidates):
                        if candidate_distances[i, j] < min_distance:
                            prob += x[i] + x[j] <= 1

            # 设置60秒超时
            solver = PULP_CBC_CMD(msg=0, timeLimit=60)
            prob.solve(solver)

            selected_indices = [i for i in range(n_candidates) if value(x[i]) == 1]
            solve_time = prob.solutionTime if hasattr(prob, 'solutionTime') else 0

            if len(selected_indices) == 0:
                st.info("整数规划未找到可行解，使用贪心算法")
                selected_indices = greedy_selection(candidates, grid, k, search_radius, enforce_spread)
        
        else:
            # 使用贪心算法
            selected_indices = greedy_selection(candidates, grid, k, search_radius, enforce_spread)

    except ImportError:
        st.info("pulp库未安装，使用贪心算法")
        selected_indices = greedy_selection(candidates, grid, k, search_radius, enforce_spread)
    except Exception as e:
        st.warning(f"优化算法出错: {e}，使用贪心算法")
        selected_indices = greedy_selection(candidates, grid, k, search_radius, enforce_spread)

    # 计算覆盖率提升
    if selected_indices:
        selected_coords = np.array([[candidates.iloc[i].geometry.x, candidates.iloc[i].geometry.y] for i in selected_indices])
        grid_coords = np.array([[g.x, g.y] for g in grid['centroid']])
        dists = cdist(selected_coords, grid_coords) * 111000
        covered = (dists <= search_radius).any(axis=0)
        weights = grid['需求量'].values if '需求量' in grid.columns else np.ones(len(grid))
        coverage_ratio = covered @ weights / total_demand
    else:
        coverage_ratio = 0.0
    
    solve_time = time.time() - start_time

    return candidates.iloc[selected_indices].copy() if selected_indices else gpd.GeoDataFrame(), coverage_ratio, solve_time

def greedy_selection(candidates, grid, k, search_radius, enforce_spread=True):
    """贪心算法选择站点 - 带分散约束"""
    if len(candidates) == 0 or len(grid) == 0:
        return []
    
    selected_indices = []
    
    # 向量化准备
    candidate_coords = np.array([[g.x, g.y] for g in candidates.geometry])
    grid_coords = np.array([[g.x, g.y] for g in grid['centroid']])
    weights = grid['需求量'].values if '需求量' in grid.columns else np.ones(len(grid))
    
    # 计算所有候选点到所有网格的距离（向量化）
    distances = cdist(candidate_coords, grid_coords) * 111000
    
    # 覆盖矩阵
    coverage = (distances <= search_radius).astype(float)
    
    # 加权覆盖
    weighted_coverage = coverage * weights
    
    # 已覆盖的网格
    covered = np.zeros(len(grid), dtype=bool)
    
    # 分散约束：最小距离1.5km
    min_distance = 1500  # 1.5km
    candidate_distances = cdist(candidate_coords, candidate_coords) * 111000
    
    for _ in range(min(k, len(candidates))):
        # 计算每个候选点的新增覆盖
        if selected_indices:
            # 排除已选点
            mask = np.ones(len(candidates), dtype=bool)
            mask[selected_indices] = False
            
            # 如果启用分散约束，排除距离已选点太近的候选点
            if enforce_spread and len(selected_indices) > 0:
                for sel_idx in selected_indices:
                    too_close = candidate_distances[sel_idx] < min_distance
                    mask = mask & ~too_close
            
            remaining_coverage = weighted_coverage[mask] * (~covered).astype(float)
            scores = remaining_coverage.sum(axis=1)
            # 创建索引映射
            available_idx = np.where(mask)[0]
            if len(scores) == 0:
                break
            best_score_idx = np.argmax(scores)
            best_idx = available_idx[best_score_idx]
            best_score = scores[best_score_idx]
        else:
            scores = weighted_coverage.sum(axis=1)
            best_idx = np.argmax(scores)
            best_score = scores[best_idx]
        
        if best_score <= 0:
            # 如果没有新增覆盖，随机选择一个未选点
            available = [i for i in range(len(candidates)) if i not in selected_indices]
            if enforce_spread:
                # 排除距离已选点太近的
                for sel_idx in selected_indices:
                    available = [i for i in available if candidate_distances[sel_idx, i] >= min_distance]
            if available:
                best_idx = np.random.choice(available)
            else:
                break
        
        selected_indices.append(best_idx)
        # 更新已覆盖网格
        covered = covered | (distances[best_idx] <= search_radius)

    return selected_indices

def calculate_metrics(grid, charging_stations, new_stations=None, search_radius=5000):
    """计算评价指标 - 使用投影坐标系进行准确距离计算"""
    all_stations = charging_stations.copy()
    if new_stations is not None and not new_stations.empty:
        all_stations = pd.concat([charging_stations, new_stations], ignore_index=True)

    # 投影到 UTM 坐标系进行距离计算
    grid_centroids_utm = gpd.GeoSeries(grid['centroid'], crs="EPSG:4326").to_crs("EPSG:32649")
    all_stations_utm = all_stations.to_crs("EPSG:32649")
    
    grid_centroids = np.array([[g.x, g.y] for g in grid_centroids_utm])
    station_coords = np.array([[g.x, g.y] for g in all_stations_utm.geometry])

    # 使用欧氏距离（UTM 投影下，单位为米）
    distances = cdist(grid_centroids, station_coords, metric='euclidean')
    min_distances = distances.min(axis=1)
    avg_distance = min_distances.mean() / 1000  # 转换为公里
    coverage_rate = (min_distances <= search_radius).mean() * 100

    sorted_distances = np.sort(min_distances)
    n = len(sorted_distances)
    cumulative = np.cumsum(sorted_distances)
    gini = (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n if cumulative[-1] > 0 else 0

    return {
        '平均可达距离(km)': avg_distance,
        '覆盖率(%)': coverage_rate,
        '基尼系数': gini,
        '站点总数': len(all_stations)
    }

def task3_comparison_map(charging_stations, new_stations, districts):
    """优化前后对比图 - 高德矢量底图"""
    if charging_stations.empty:
        st.warning("暂无充电站数据")
        return

    try:
        center_lat = charging_stations.geometry.y.mean()
        center_lon = charging_stations.geometry.x.mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=None
        )

        # 添加高德矢量底图
        folium.TileLayer(
            tiles='https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            attr="高德地图",
            name="高德矢量图"
        ).add_to(m)

        if not districts.empty:
            folium.GeoJson(
                districts,
                style_function=lambda x: {
                    'fillColor': 'rgba(30, 136, 229, 0.08)',
                    'color': '#1e88e5',
                    'weight': 1,
                    'fillOpacity': 0.08
                }
            ).add_to(m)

        # 现有充电站 - 蓝色标记
        for _, row in charging_stations.iterrows():
            folium.CircleMarker(
                location=[row['纬度'], row['经度']],
                radius=6,
                color='#1e88e5',
                fill=True,
                fill_color='#42a5f5',
                fill_opacity=0.8,
                popup=folium.Popup(f"<strong>现有站点</strong><br>{row['名称']}", max_width=200)
            ).add_to(m)

        # 新增站点 - 亮绿色大号标记 + 缓冲区
        if new_stations is not None and not new_stations.empty:
            for idx, row in new_stations.iterrows():
                lat, lon = row.geometry.y, row.geometry.x
                
                # 添加服务范围缓冲区（1.5km半径）
                folium.Circle(
                    location=[lat, lon],
                    radius=1500,  # 1.5km
                    color='#3fb950',
                    fill=True,
                    fill_color='#3fb950',
                    fill_opacity=0.15,
                    weight=2,
                    popup=folium.Popup(f"<strong>服务范围</strong><br>半径: 1.5km", max_width=200)
                ).add_to(m)
                
                # 添加亮绿色大号标记
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=12,
                    color='#22c55e',
                    fill=True,
                    fill_color='#4ade80',
                    fill_opacity=0.95,
                    weight=3,
                    popup=folium.Popup(f"<strong>新增站点 {idx+1}</strong><br>坐标: {lat:.4f}, {lon:.4f}", max_width=200)
                ).add_to(m)

        legend_html = '''
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; background: rgba(22, 27, 34, 0.95); padding: 18px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.5); border: 1px solid #30363d;">
            <h4 style="color: #ffffff; margin-bottom: 12px; font-size: 16px;">图例</h4>
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <div style="width: 12px; height: 12px; background: #42a5f5; border-radius: 50%; border: 2px solid #1e88e5; margin-right: 12px;"></div>
                <span style="color: #c9d1d9; font-size: 15px;">现有充电站</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 14px; height: 14px; background: #26a69a; border-radius: 50%; border: 2px solid #3fb950; margin-right: 12px;"></div>
                <span style="color: #c9d1d9; font-size: 15px;">新增充电站</span>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        folium.LayerControl().add_to(m)

        folium_static(m, width=4000, height=750)

    except Exception as e:
        st.error(f"优化前后对比图加载失败: {e}")

def task3_new_stations_map(new_stations, districts):
    """新增站点地图 - 高德"""
    if new_stations is None or new_stations.empty:
        st.warning("暂无新增站点数据")
        return

    try:
        center_lat = new_stations.geometry.y.mean()
        center_lon = new_stations.geometry.x.mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles=None
        )

        # 添加高德矢量底图（不带API key，提高兼容性）
        folium.TileLayer(
            tiles='https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
            attr="高德地图",
            name="高德矢量图"
        ).add_to(m)
        
        # 添加OpenStreetMap作为fallback
        folium.TileLayer(
            tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            attr="OpenStreetMap",
            name="OpenStreetMap"
        ).add_to(m)

        if not districts.empty:
            folium.GeoJson(
                districts,
                style_function=lambda x: {
                    'fillColor': 'rgba(30, 136, 229, 0.08)',
                    'color': '#1e88e5',
                    'weight': 1,
                    'fillOpacity': 0.08
                }
            ).add_to(m)

        for idx, row in new_stations.iterrows():
            # 添加1.5km服务范围缓冲区（半透明绿圈）
            folium.Circle(
                location=[row.geometry.y, row.geometry.x],
                radius=1500,  # 1.5km
                color='#00FF00',
                fill=True,
                fill_color='#00FF00',
                fill_opacity=0.15,
                weight=2
            ).add_to(m)
            
            popup_html = f"""
            <div style='color: #1a237e; padding: 12px; background: white; border-radius: 8px;'>
                <h4 style='color: #3fb950; margin-bottom: 8px;'>新增站点 {idx + 1}</h4>
                <p style='margin: 6px 0; font-size: 14px;'><strong>坐标:</strong> {row.geometry.y:.4f}, {row.geometry.x:.4f}</p>
                <p style='margin: 6px 0; font-size: 14px;'><strong>类型:</strong> {row.get('type', '未知')}</p>
                <p style='margin: 6px 0; font-size: 14px;'><strong>服务范围:</strong> 1.5km</p>
            </div>
            """
            # 亮绿色大号marker
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=14,
                color='#22c55e',
                fill=True,
                fill_color='#4ade80',
                fill_opacity=0.95,
                popup=folium.Popup(popup_html, max_width=250),
                weight=3
            ).add_to(m)

        folium.LayerControl().add_to(m)

        folium_static(m, width=4000, height=750)

    except Exception as e:
        st.error(f"新增站点地图加载失败: {e}")

def task3_metrics_table(before_metrics, after_metrics):
    """指标对比表"""
    # 计算变化值
    distance_diff = before_metrics['平均可达距离(km)'] - after_metrics['平均可达距离(km)']
    coverage_diff = after_metrics['覆盖率(%)'] - before_metrics['覆盖率(%)']
    gini_diff = after_metrics['基尼系数'] - before_metrics['基尼系数']
    station_diff = after_metrics['站点总数'] - before_metrics['站点总数']
    
    metrics_df = pd.DataFrame({
        '指标': ['平均可达距离(km)', '覆盖率(%)', '基尼系数', '站点总数'],
        '优化前': [
            f"{before_metrics['平均可达距离(km)']:.2f}",
            f"{before_metrics['覆盖率(%)']:.1f}",
            f"{before_metrics['基尼系数']:.3f}",
            before_metrics['站点总数']
        ],
        '优化后': [
            f"{after_metrics['平均可达距离(km)']:.2f}",
            f"{after_metrics['覆盖率(%)']:.1f}",
            f"{after_metrics['基尼系数']:.3f}",
            after_metrics['站点总数']
        ],
        '变化': [
            f"-{distance_diff:.2f}" if distance_diff > 0 else f"+{-distance_diff:.2f}",
            f"+{coverage_diff:.1f}" if coverage_diff > 0 else f"{coverage_diff:.1f}",
            f"{gini_diff:+.3f}",
            f"+{station_diff}"
        ]
    })

    # 创建紧凑的柱形图
    fig = go.Figure(data=[
        go.Bar(name='优化前', x=metrics_df['指标'][:3],
               y=[before_metrics['平均可达距离(km)'], before_metrics['覆盖率(%)'], before_metrics['基尼系数']],
               marker_color='#42a5f5',
               marker_line_color='#1e88e5',
               marker_line_width=1.5,
               width=0.35,
               text=[f"{v:.2f}" for v in [before_metrics['平均可达距离(km)'], before_metrics['覆盖率(%)'], before_metrics['基尼系数']]],
               textposition='auto',
               textfont=dict(color='#ffffff', size=11)),
        go.Bar(name='优化后', x=metrics_df['指标'][:3],
               y=[after_metrics['平均可达距离(km)'], after_metrics['覆盖率(%)'], after_metrics['基尼系数']],
               marker_color='#26a69a',
               marker_line_color='#3fb950',
               marker_line_width=1.5,
               width=0.35,
               text=[f"{v:.2f}" for v in [after_metrics['平均可达距离(km)'], after_metrics['覆盖率(%)'], after_metrics['基尼系数']]],
               textposition='auto',
               textfont=dict(color='#ffffff', size=11))
    ])
    
    # 设置坐标轴范围
    max_distance = max(before_metrics['平均可达距离(km)'], after_metrics['平均可达距离(km)'])
    max_coverage = max(before_metrics['覆盖率(%)'], after_metrics['覆盖率(%)'], 100)
    max_gini = max(before_metrics['基尼系数'], after_metrics['基尼系数'], 1)
    
    fig.update_layout(
        title='优化前后指标对比',
        barmode='group',
        paper_bgcolor='rgba(13, 17, 23, 0.95)',
        plot_bgcolor='rgba(13, 17, 23, 0.95)',
        font_color='#ffffff',
        title_font_size=22,
        title_font_color='#ffffff',
        title_x=0.5,
        xaxis_title_font_color='#c9d1d9',
        yaxis_title_font_color='#c9d1d9',
        xaxis_tickfont=dict(color='#c9d1d9', size=13),
        yaxis_tickfont=dict(color='#c9d1d9', size=12),
        margin=dict(l=20, r=20, t=50, b=30),
        height=380,  # 紧凑的图表高度
        legend=dict(
            title='状态',
            title_font_color='#c9d1d9',
            font_color='#c9d1d9',
            bgcolor='rgba(22, 27, 34, 0.9)',
            bordercolor='#30363d',
            borderwidth=1,
            x=0.95,
            y=1.05,
            xanchor='right',
            orientation='h'
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(22, 27, 34, 0.95)',
            bordercolor='#42a5f5',
            font_color='#ffffff'
        )
    )
    
    # 添加网格线
    fig.update_yaxes(
        gridcolor='rgba(79, 89, 107, 0.3)',
        gridwidth=1,
        showline=True,
        linecolor='#30363d'
    )
    fig.update_xaxes(
        showline=True,
        linecolor='#30363d'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 美化表格显示
    st.subheader("指标对比详情")
    
    # 使用 Streamlit 的原生表格样式，避免 jinja2 依赖问题
    st.dataframe(metrics_df, use_container_width=True, height=220)
    
    # 添加表格说明
    st.markdown("""
    <div style="background: rgba(22, 27, 34, 0.9); padding: 15px; border-radius: 8px; margin-top: 10px;">
        <p style="color: #8b949e; font-size: 13px;">
            <strong>优化前</strong>：现有充电站的服务指标；
            <strong>优化后</strong>：新增站点后的服务指标；
            <strong>变化</strong>：优化带来的改善（+表示提升，-表示下降）
        </p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.markdown("""
        <style>
        #main-title {
            font-size: 80px !important;
            font-weight: 900 !important;
            color: #1e88e5 !important;
            text-align: center !important;
            margin-bottom: 50px !important;
            line-height: 1.2 !important;
            letter-spacing: 2px !important;
        }
        </style>
        <div id="main-title">西安市新能源汽车充电设施供需匹配与选址优化系统</div>
    """, unsafe_allow_html=True)

    with st.spinner("正在加载数据，请稍候..."):
        charging_stations, districts, city_boundary, roads, population, poi_df = load_data()

    show_stats_cards(charging_stations, districts)

    with st.sidebar:
        st.markdown("<h2 style='color: #1e88e5; margin-bottom: 25px; font-size: 22px;'>功能菜单</h2>", unsafe_allow_html=True)

        task_choice = st.radio("选择任务模块", ["任务一：空间分布测度", "任务二：供需匹配量化", "任务三：选址优化"], index=0)

        if task_choice == "任务一：空间分布测度":
            task1_option = st.selectbox("选择分析项", ["充电站分布图", "区县密度图", "运营商统计图"])

        elif task_choice == "任务二：供需匹配量化":
            task2_option = st.selectbox("选择分析项", ["网格供需得分图", "冷热点分析图", "服务盲区地图"])
            search_radius = st.slider("搜索半径(km)", 3, 10, 5, 1, help="2SFCA模型的搜索半径参数")
            deficit_threshold = st.slider("供给不足阈值百分位数", 0.1, 0.5, 0.2, 0.05, 
                                        help="供需得分低于此百分位数的网格判定为供给不足区")

        elif task_choice == "任务三：选址优化":
            task3_option = st.selectbox("选择分析项", ["优化前后对比图", "新增站点地图", "指标对比表"])
            new_stations_num = st.slider("新增站点数量", 3, 10, 5, 1, help="待选址的充电站数量")
            enforce_spread = st.checkbox("强制分散", value=True, help="开启后新增站点之间至少保持1.5km距离")
            solver_method = st.selectbox("求解方法", ["贪心启发式", "整数规划"], index=0, 
                                        help="贪心启发式速度快，整数规划更精确但可能耗时较长")
            deficit_threshold = st.slider("供给不足阈值百分位数", 0.1, 0.5, 0.2, 0.05,
                                        help="供需得分低于此百分位数的网格判定为供给不足区")

    if task_choice == "任务一：空间分布测度":
        st.markdown("<div class='animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #ffffff; margin-bottom: 25px; font-size: 28px;'>任务一：空间分布测度</h2>", unsafe_allow_html=True)

        if task1_option == "充电站分布图":
            st.markdown("### 充电站分布图")
            st.markdown("显示西安市所有充电站的位置分布，点击标记可查看详细信息（运营商、端口数等）。")
            task1_charging_map(charging_stations, districts)

        elif task1_option == "区县密度图":
            st.markdown("### 区县密度图")
            st.markdown("展示各区县充电站的分布密度（充电站数量/区县面积），颜色越深表示密度越高。")
            task1_density_map(charging_stations, districts)

        elif task1_option == "运营商统计图":
            st.markdown("### 运营商统计图")
            st.markdown("统计各运营商在西安市的充电站数量分布，便于了解市场竞争格局。")
            task1_operator_chart(charging_stations)
        st.markdown("</div>", unsafe_allow_html=True)

    elif task_choice == "任务二：供需匹配量化":
        st.markdown("<div class='animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #ffffff; margin-bottom: 25px; font-size: 28px;'>任务二：供需匹配量化</h2>", unsafe_allow_html=True)

        with st.spinner("正在计算供需匹配..."):
            grid = create_grid(city_boundary)
            grid = calculate_supply_demand(charging_stations, grid, poi_df)
            grid, _ = calculate_2sfca(grid, charging_stations, search_radius * 1000)
            
            # 使用用户设置的阈值判定供给不足区
            threshold_value = grid['供需得分'].quantile(deficit_threshold)
            grid['供给状态'] = grid['供需得分'].apply(lambda x: '供给不足' if x <= threshold_value else '供给充足')

        if task2_option == "网格供需得分图":
            st.markdown("### 网格供需得分图")
            st.markdown("基于2SFCA模型计算的1km×1km网格供需匹配得分分布。红色表示供给不足，绿色表示供给充足。")
            task2_supply_demand_map(grid)

        elif task2_option == "冷热点分析图":
            st.markdown("### 冷热点分析图")
            st.markdown("使用局部Getis-Ord Gi*统计量识别充电站供需的热点区域（高值聚集）和冷点区域（低值聚集）。")
            task2_hotspot_map(grid)

        elif task2_option == "服务盲区地图":
            st.markdown("### 服务盲区地图")
            st.markdown(f"识别供需得分最低的{int(deficit_threshold*100)}%网格作为服务盲区，显示为红色区域，支持下载GeoJSON文件。")
            task2_blind_area_map(grid, charging_stations, districts, deficit_threshold)
        st.markdown("</div>", unsafe_allow_html=True)

    elif task_choice == "任务三：选址优化":
        st.markdown("<div class='animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #ffffff; margin-bottom: 25px; font-size: 28px;'>任务三：选址优化</h2>", unsafe_allow_html=True)

        # 检查参数是否变化，决定是否重新计算
        params_key = f"{new_stations_num}_{solver_method}_{enforce_spread}_{deficit_threshold}"
        needs_recalc = (
            'task3_results' not in st.session_state or
            st.session_state.get('task3_params') != params_key
        )

        if needs_recalc:
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # 步骤1: 创建网格
                status_text.text("正在创建网格...")
                progress_bar.progress(10)
                grid = create_grid(city_boundary)
                st.info(f"网格数量: {len(grid)}")

                # 步骤2: 计算供需
                status_text.text("正在计算供需...")
                progress_bar.progress(30)
                grid = calculate_supply_demand(charging_stations, grid, poi_df)

                # 步骤3: 2SFCA分析
                status_text.text("正在进行2SFCA分析...")
                progress_bar.progress(50)
                grid, _ = calculate_2sfca(grid, charging_stations, 5000)

                # 步骤4: 生成候选点
                status_text.text("正在生成候选点...")
                progress_bar.progress(70)
                threshold = grid['供需得分'].quantile(deficit_threshold)
                blind_areas = grid[grid['供需得分'] <= threshold]
                candidates = generate_candidates(blind_areas, roads, charging_stations, city_boundary)
                st.info(f"候选点数量: {len(candidates)}")

                # 步骤5: 选址优化
                status_text.text("正在进行选址优化...")
                progress_bar.progress(85)
                
                # 转换求解方法参数
                solver_type = 'greedy' if solver_method == '贪心启发式' else 'integer'
                new_stations, coverage_ratio, solve_time = optimize_locations(
                    candidates, grid, 
                    k=new_stations_num, 
                    solver_method=solver_type,
                    enforce_spread=enforce_spread
                )
                st.info(f"求解耗时: {solve_time:.2f}秒")

                # 步骤6: 计算指标
                status_text.text("正在计算评价指标...")
                progress_bar.progress(95)
                before_metrics = calculate_metrics(grid, charging_stations)
                after_metrics = calculate_metrics(grid, charging_stations, new_stations)

                # 完成
                progress_bar.progress(100)
                status_text.text("计算完成！")

                # 缓存结果
                st.session_state['task3_results'] = {
                    'grid': grid,
                    'new_stations': new_stations,
                    'coverage_ratio': coverage_ratio,
                    'solve_time': solve_time,
                    'before_metrics': before_metrics,
                    'after_metrics': after_metrics
                }
                st.session_state['task3_params'] = params_key

            except Exception as e:
                st.error(f"计算出错: {e}")
                st.session_state['task3_results'] = {
                    'grid': None,
                    'new_stations': gpd.GeoDataFrame(),
                    'coverage_ratio': 0.0,
                    'before_metrics': None,
                    'after_metrics': None
                }
                st.session_state['task3_params'] = params_key
        else:
            # 使用缓存的结果
            results = st.session_state['task3_results']
            new_stations = results['new_stations']
            coverage_ratio = results['coverage_ratio']
            solve_time = results.get('solve_time', 0.0)
            before_metrics = results['before_metrics']
            after_metrics = results['after_metrics']
            st.info("使用缓存结果，如需重新计算请修改参数")
        
        # 显示优化指标卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("优化覆盖率", f"{coverage_ratio*100:.1f}%")
        with col2:
            if before_metrics and after_metrics:
                distance_improve = (before_metrics['平均可达距离(km)'] - after_metrics['平均可达距离(km)']) / before_metrics['平均可达距离(km)'] * 100
                st.metric("平均距离改善", f"{distance_improve:.1f}%")
            else:
                st.metric("平均距离改善", "N/A")
        with col3:
            st.metric("新增站点数量", len(new_stations))
        with col4:
            st.metric("求解耗时", f"{solve_time:.2f}秒")

        if task3_option == "优化前后对比图":
            st.markdown("### 优化前后对比图")
            st.markdown("蓝色标记为现有充电站，绿色标记为新增优化站点，直观展示选址优化效果。")
            task3_comparison_map(charging_stations, new_stations, districts)

        elif task3_option == "新增站点地图":
            st.markdown("### 新增站点地图")
            st.markdown("显示通过优化算法筛选出的新增充电站位置，点击标记可查看详细坐标信息。")
            task3_new_stations_map(new_stations, districts)

        elif task3_option == "指标对比表":
            st.markdown("### 指标对比表")
            st.markdown("对比优化前后的平均可达距离、覆盖率和基尼系数，量化评估选址优化效果。")
            task3_metrics_table(before_metrics, after_metrics)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
