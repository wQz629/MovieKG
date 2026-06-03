"""
中文电影知识图谱构建与挖掘 - 主运行脚本
知识图谱构建与挖掘实践 (《大数据原理与技术》结课项目)

运行: python main.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils import ensure_dirs, print_section

import time
start_time = time.time()


def run_step(step_name, module_name, func_name="main"):
    """运行单个步骤"""
    print(f"\n>>> 运行: {step_name}")
    
    step_start = time.time()
    
    module = __import__(f"src.{module_name}", fromlist=[func_name])
    
    if hasattr(module, func_name):
        result = getattr(module, func_name)()
    else:
        result = None
    
    elapsed = time.time() - step_start
    print(f"<<< {step_name} 完成 (耗时: {elapsed:.1f} 秒)")
    
    return result


def main():
    """主流程"""
    ensure_dirs()
    print("=" * 50)
    print("  中文电影知识图谱构建与挖掘")
    print("  《大数据原理与技术》结课项目")
    print("=" * 50)
    
    run_step("数据采集", "01_data_collection", "collect_data")
    run_step("数据预处理 + 三元组构建", "02_data_preprocessing", "preprocess")
    run_step("实体识别", "03_entity_recognition", "recognize_entities")
    run_step("关系抽取", "04_relation_extraction", "extract_relations")
    run_step("知识图谱导入", "05_kg_import", "kg_import")
    run_step("查询与可视化", "06_visualization", "visualize")
    run_step("知识挖掘分析", "07_knowledge_mining", "mine")
    
    total_time = time.time() - start_time
    print()
    print("=" * 50)
    print(f"  项目运行完成！总耗时: {total_time:.1f} 秒")
    print("=" * 50)
    print()
    print("  输出目录:")
    print("    - 处理数据: data/processed/")
    print("    - 统计图表: output/visualization/")
    print("    - 挖掘结果: output/mining_results/")
    print("    - 交互式可视化: output/visualization/kg_visualization.html")
    print()


if __name__ == "__main__":
    main()
