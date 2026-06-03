"""
第4步：关系抽取
- 从描述文本中提取实体之间的关系
- 使用基于规则的模式匹配
- 补充关系类型
- 输出：补充后的三元组数据
"""
import sys
sys.path.insert(0, str(__file__).replace("04_relation_extraction.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import re
import ast


# 预定义的关系提取模式
RELATION_PATTERNS = [
    # 导演-电影关系
    (r"由(.{1,10})执导", "执导", "导演"),
    (r"导演(.{1,10})", "执导", "导演"),
    
    # 主演关系
    (r"由(.{1,20})主演", "主演", "演员"),
    (r"主演(.{1,20})", "主演", "演员"),
    (r"(.{1,10})主演", "主演", "演员"),
    
    # 合作关系
    (r"与(.{1,10})合作", "合作", "演员"),
    (r"和(.{1,10})共同", "合作", "演员"),
    
    # 改编关系
    (r"改编自(.{1,20})", "改编自", "作品"),
    (r"根据(.{1,20})改编", "改编自", "作品"),
    
    # 时间关系
    (r"(\d{4})年", "发生年代", "年份"),
]


def extract_relations_by_pattern(text, movie_title, known_entities):
    """
    使用正则模式从文本中抽取关系
    返回 [(head, relation, tail, tail_type), ...]
    """
    if not text or not isinstance(text, str):
        return []
    
    relations = []
    
    for pattern, relation, tail_type in RELATION_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            match = match.strip()
            if match and len(match) >= 2:
                relations.append((movie_title, relation, match, tail_type))
    
    # 检查文本中是否包含已知实体对
    # 例如：某电影的描述中提到另一部电影
    for ent_type, ent_list in known_entities.items():
        if ent_type == "电影":
            for other_movie in ent_list:
                if other_movie != movie_title and other_movie in text:
                    relations.append((movie_title, "提及", other_movie, "电影"))
    
    return relations


def extract_relations():
    """主流程"""
    print_section("第4步：关系抽取")
    
    df = load_csv_data("movies_with_entities.csv")
    if df is None:
        print("  从样例数据加载...")
        df = load_sample_data()
    else:
        print(f"  加载 {len(df)} 条记录")
    
    df_triples = load_csv_data("triples.csv")
    if df_triples is None:
        print("  未找到已有三元组")
        return
    
    known_entities = {
        "电影": df["title"].dropna().unique().tolist(),
        "导演": df["director"].dropna().unique().tolist(),
        "演员": [],
        "类型": [],
        "国家": df["country"].dropna().unique().tolist(),
    }
    
    all_actors = set()
    for actors in df["actors"]:
        if isinstance(actors, str):
            if actors.startswith("["):
                try:
                    actors_list = ast.literal_eval(actors)
                except:
                    actors_list = [actors]
            else:
                actors_list = [x.strip() for x in actors.split(",")]
        elif isinstance(actors, list):
            actors_list = actors
        else:
            actors_list = []
        for a in actors_list:
            if a and str(a).strip():
                all_actors.add(str(a).strip())
    known_entities["演员"] = list(all_actors)
    
    all_genres = set()
    for genres in df["genres"]:
        if isinstance(genres, str):
            if genres.startswith("["):
                try:
                    genres_list = ast.literal_eval(genres)
                except:
                    genres_list = [genres]
            else:
                genres_list = [x.strip() for x in genres.split(",")]
        elif isinstance(genres, list):
            genres_list = genres
        else:
            genres_list = []
        for g in genres_list:
            if g and str(g).strip():
                all_genres.add(str(g).strip())
    known_entities["类型"] = list(all_genres)
    
    new_relations = []
    for _, row in df.iterrows():
        movie = row["title"]
        desc = row.get("description", "")
        if desc:
            extra = extract_relations_by_pattern(desc, movie, known_entities)
            new_relations.extend(extra)
    
    print(f"  从描述文本中抽取了 {len(new_relations)} 条额外关系")
    
    if new_relations:
        df_new = pd.DataFrame(new_relations,
                              columns=["head", "relation", "tail", "tail_type"])
        df_new["head_type"] = "电影"
        df_new["movie_id"] = ""
        
        df_triples = pd.concat([df_triples, df_new], ignore_index=True)
        df_triples = df_triples.drop_duplicates(subset=["head", "relation", "tail"], keep="first")
    
    save_csv_data(df_triples, "triples_enriched.csv")
    
    print(f"  关系抽取完成！总共 {len(df_triples)} 条三元组")
    return df_triples


if __name__ == "__main__":
    triples = extract_relations()
    
    print("\n抽取的关系示例 (前10条):")
    print(triples.head(10).to_string())
