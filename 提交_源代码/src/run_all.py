"""
主执行脚本
按顺序执行所有分析模块
"""
import subprocess
import sys
import importlib
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
config = importlib.import_module('00_config')

def run_module(module_name):
    """
    运行指定模块
    
    参数:
        module_name: 模块名称
    """
    print(f"\n{'='*60}")
    print(f"运行模块: {module_name}")
    print('='*60)
    
    try:
        module = importlib.import_module(module_name)
        module.main()
        return True
    except Exception as e:
        print(f"模块 {module_name} 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主函数：按顺序执行所有模块
    """
    print("=" * 60)
    print("西安市新能源汽车充电设施供需匹配与选址优化")
    print("=" * 60)
    
    modules = [
        '01_preprocess_poi',
        '02_spatial_matching',
        '03_regional_analysis',
        '04_supply_demand_model',
        '05_location_optimization',
        '06_evaluation',
        '07_generate_report'
    ]
    
    success_count = 0
    for module in modules:
        if run_module(module):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"执行完成: {success_count}/{len(modules)} 个模块成功")
    print(f"输出目录: {config.OUTPUT_DIR}")
    print(f"最终报告: {config.BASE_DIR / 'final_report.md'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
