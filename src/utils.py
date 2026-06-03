"""
工具函数模块 - 公共工具函数
"""
import json
import os
import pandas as pd
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 路径配置
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SAMPLE_DATA_DIR = PROJECT_ROOT / "data" / "sample_data"
OUTPUT_DIR = PROJECT_ROOT / "output"
MINING_RESULTS_DIR = OUTPUT_DIR / "mining_results"
VIZ_DIR = OUTPUT_DIR / "visualization"


def ensure_dirs():
    """确保所有必要的目录存在"""
    for d in [DATA_RAW_DIR, DATA_PROCESSED_DIR, SAMPLE_DATA_DIR, 
              MINING_RESULTS_DIR, VIZ_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_sample_data():
    """加载内置样例数据"""
    sample_file = SAMPLE_DATA_DIR / "movie_sample_data.json"
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def load_csv_data(filename, search_dirs=None):
    """从目录加载CSV数据，依次搜索 raw -> processed
    Args:
        filename: CSV文件名
        search_dirs: 要搜索的目录列表，默认先搜raw再搜processed
    """
    if search_dirs is None:
        search_dirs = [DATA_RAW_DIR, DATA_PROCESSED_DIR]
    for d in search_dirs:
        filepath = d / filename
        if filepath.exists():
            return pd.read_csv(filepath, encoding="utf-8")
    return None


def save_csv_data(df, filename, subdir="processed"):
    """保存CSV数据"""
    if subdir == "processed":
        filepath = DATA_PROCESSED_DIR / filename
    else:
        filepath = DATA_RAW_DIR / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath


def save_json_data(data, filename, subdir="processed"):
    """保存JSON数据"""
    if subdir == "processed":
        filepath = DATA_PROCESSED_DIR / filename
    else:
        filepath = DATA_RAW_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def print_section(title):
    """打印分区标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
