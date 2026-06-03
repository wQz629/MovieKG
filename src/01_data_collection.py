"""
第1步：数据采集
- 优先加载TMDB 5000外部数据（两个文件：movies + credits）
- 如果TMDB数据不存在，回退到内置样例数据
- 输出：原始数据 DataFrame
"""
import sys
sys.path.insert(0, str(__file__).replace("01_data_collection.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import ast


def load_tmdb_movies():
    """加载TMDB 5000电影数据"""
    df = load_csv_data("tmdb_5000_movies.csv")
    if df is None:
        return None, False
    
    print(f"  [TMDB] 加载电影数据: {len(df)} 条")
    
    # 解析genres (JSON格式字符串 -> 列表)
    def parse_genres(genre_str):
        try:
            if isinstance(genre_str, str):
                genres = ast.literal_eval(genre_str)
                return [g["name"] for g in genres]
            return []
        except:
            return []
    
    # 解析年份
    def parse_year(date_str):
        try:
            if isinstance(date_str, str) and len(date_str) >= 4:
                return int(date_str[:4])
            return 0
        except:
            return 0
    
    # 解析制片国家
    def parse_countries(country_str):
        try:
            if isinstance(country_str, str):
                countries = ast.literal_eval(country_str)
                names = [c["name"] for c in countries if "name" in c]
                return names[0] if names else "未知"
            return "未知"
        except:
            return "未知"
    
    # 构建统一格式
    records = []
    for _, row in df.iterrows():
        records.append({
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "year": parse_year(row.get("release_date", "")),
            "rating": row.get("vote_average", 0),
            "director": "",  # 从credits补充
            "actors": [],    # 从credits补充
            "genres": parse_genres(row.get("genres", "[]")),
            "country": parse_countries(row.get("production_countries", "[]")),
            "description": row.get("overview", ""),
        })
    
    return pd.DataFrame(records), True


def load_tmdb_credits(df_movies):
    """加载TMDB credits数据并合并到电影数据中"""
    df_credits = load_csv_data("tmdb_5000_credits.csv")
    if df_credits is None:
        print("  [TMDB] 未找到credits文件，跳过演员/导演信息补充")
        return df_movies
    
    print(f"  [TMDB] 加载演职人员数据: {len(df_credits)} 条")
    
    # 构建 movie_id -> credits 映射
    credit_map = {}
    for _, row in df_credits.iterrows():
        movie_id = row.get("movie_id", row.get("id", ""))
        # 尝试多种可能的列名
        if not movie_id:
            for col in df_credits.columns:
                if "id" in col.lower():
                    movie_id = row[col]
                    break
        credit_map[str(movie_id)] = {
            "cast": row.get("cast", "[]"),
            "crew": row.get("crew", "[]"),
        }
    
    # 解析并合并
    def parse_cast(cast_str):
        try:
            if isinstance(cast_str, str):
                cast = ast.literal_eval(cast_str)
                return [c["name"] for c in cast[:5] if "name" in c]
            return []
        except:
            return []
    
    def find_director(crew_str):
        try:
            if isinstance(crew_str, str):
                crew = ast.literal_eval(crew_str)
                for c in crew:
                    if c.get("job") == "Director":
                        return c.get("name", "")
            return ""
        except:
            return ""
    
    # 合并数据
    filled_director = 0
    filled_actors = 0
    for idx, row in df_movies.iterrows():
        mid = str(row["id"])
        if mid in credit_map:
            credits = credit_map[mid]
            actors = parse_cast(credits["cast"])
            if actors:
                df_movies.at[idx, "actors"] = actors
                filled_actors += 1
            director = find_director(credits["crew"])
            if director:
                df_movies.at[idx, "director"] = director
                filled_director += 1
    
    print(f"  [TMDB] 已补充导演信息: {filled_director} 部, 演员信息: {filled_actors} 部")
    
    return df_movies


def collect_data():
    """采集电影数据"""
    print_section("第1步：数据采集")
    
    result = load_tmdb_movies()
    
    if result is not None and result[1]:
        df_tmdb, _ = result
        df_tmdb = load_tmdb_credits(df_tmdb)
        
        before = len(df_tmdb)
        df_tmdb = df_tmdb[df_tmdb["director"].str.len() > 0].copy()
        after = len(df_tmdb)
        print(f"  [过滤] 移除无导演信息的电影: {before - after} 部")
        
        df_combined = df_tmdb
        print(f"  使用TMDB数据: {len(df_combined)} 部电影")
    else:
        print("  [回退] TMDB数据未找到，使用内置样例数据...")
        df_sample = load_sample_data()
        print(f"  使用样例数据: {len(df_sample)} 部电影")
        df_combined = df_sample
    
    save_csv_data(df_combined, "movies_raw.csv", subdir="raw")
    print(f"  数据采集完成！共 {len(df_combined)} 部电影")
    
    return df_combined


if __name__ == "__main__":
    df = collect_data()
    print("\n数据预览:")
    print(df[["title", "year", "rating", "director"]].head(10).to_string())
