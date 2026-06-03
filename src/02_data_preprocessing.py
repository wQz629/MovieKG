"""
第2步：数据预处理 + 三元组构建
- 数据清洗（去重、缺失值处理、格式规范化）
- 中文分词 (jieba) + 关键词提取
- 构建三元组 (head, relation, tail)
- 输出：清洗后的数据和三元组文件
"""
import sys
sys.path.insert(0, str(__file__).replace("02_data_preprocessing.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import numpy as np
import jieba
import jieba.analyse
import ast


def clean_data(df):
    """清洗数据"""
    print("  [清洗] 开始数据清洗...")
    
    # 1. 处理年份
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    
    # 2. 处理评分
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
    
    # 3. 处理类型（genres）：如果是字符串列表如 "['剧情', '喜剧']"，转换为列表
    def parse_genres(g):
        if isinstance(g, str):
            if g.startswith("["):
                try:
                    return ast.literal_eval(g)
                except:
                    return [g]
            else:
                return [g.strip()]
        elif isinstance(g, list):
            return g
        return []
    
    df["genres"] = df["genres"].apply(parse_genres)
    
    # 4. 处理演员（actors）：同上
    def parse_actors(a):
        if isinstance(a, str):
            if a.startswith("["):
                try:
                    return ast.literal_eval(a)
                except:
                    return [a]
            else:
                return [x.strip() for x in a.split(",")]
        elif isinstance(a, list):
            return a
        return []
    
    if "actors" in df.columns:
        df["actors"] = df["actors"].apply(parse_actors)
    
    # 5. 填充缺失值
    df["title"] = df["title"].fillna("未知电影")
    df["director"] = df["director"].fillna("未知导演")
    df["country"] = df["country"].fillna("未知")
    df["description"] = df["description"].fillna("")
    
    # 6. 去重
    before = len(df)
    df = df.drop_duplicates(subset=["title"], keep="first")
    after = len(df)
    if before > after:
        print(f"  [去重] 移除 {before - after} 条重复数据")
    
    print(f"  ✓ 清洗完成: {len(df)} 条记录")
    return df


def extract_keywords(text, topK=5):
    """提取关键词（自动判断语言：中文用jieba，英文用简单词频）"""
    if not text or not isinstance(text, str):
        return []
    
    # 判断是否为英文文本（超过50%字符为ascii字母）
    ascii_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total_chars = sum(1 for c in text if c.isalpha())
    
    if total_chars > 0 and ascii_chars / total_chars > 0.5:
        # 英文文本：提取大写单词（通常是专有名词/重要词）+ 高频词
        import re
        words = re.findall(r'[A-Z][a-z]+', text)
        # 去重并按长度排序（较长的词通常更重要）
        unique_words = list(dict.fromkeys(words))  # 保持顺序去重
        # 过滤掉太短的词和常见英文停用词
        stop_words = {
            'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where',
            'Which', 'Who', 'Whom', 'Whose', 'How', 'Why', 'There', 'Their',
            'They', 'Them', 'Their', 'Its', 'It', 'His', 'Her', 'Him', 'She',
            'He', 'With', 'Without', 'About', 'Into', 'From', 'After', 'Before',
            'During', 'Through', 'Over', 'Under', 'Between', 'Among', 'Within',
            'While', 'Where', 'Upon', 'Here', 'Then', 'Than', 'Also', 'Just',
            'But', 'And', 'Not', 'Are', 'Was', 'Were', 'Been', 'Being', 'Have',
            'Has', 'Had', 'Having', 'Does', 'Did', 'Doing', 'Will', 'Would',
            'Could', 'Should', 'May', 'Might', 'Must', 'Can', 'Been', 'Some',
            'Any', 'Every', 'Each', 'Both', 'All', 'Many', 'Much', 'Most',
            'Few', 'Several', 'Only', 'Very', 'Too', 'So', 'Such', 'More',
            'Yet', 'Already', 'Still', 'Even', 'Well', 'Ever', 'Never', 'Along',
            'Away', 'Back', 'Down', 'Up', 'Out', 'Off', 'On', 'In', 'At',
            'Because', 'Since', 'Until', 'Once', 'Though', 'Although', 'Like',
            'Also', 'Another', 'Other', 'Often', 'Finally', 'Eventually', 'Together',
            'A', 'An', 'Is', 'His', 'Her', 'Its', 'Our', 'Your', 'My', 'Am',
            'Are', 'Was', 'Were', 'Being', 'Been', 'Around', 'Across', 'Almost',
            'Always', 'Best', 'Better', 'Big', 'Former', 'Great', 'Following',
            'Instead', 'Long', 'Made', 'Meanwhile', 'New', 'Next', 'Old',
            'Part', 'Plus', 'Real', 'Right', 'Same', 'Set', 'Short', 'Soon',
            'Still', 'Such', 'Sure', 'Tell', 'Told', 'Tells', 'Top', 'Unable',
            'Use', 'Used', 'Using', 'Various', 'Way', 'Whole', 'Willing', 'Within',
            'Without', 'Worth', 'Young',
        }
        unique_words = [w for w in unique_words if len(w) > 2 and w not in stop_words]
        return unique_words[:topK]
    else:
        # 中文文本：使用jieba
        try:
            keywords = jieba.analyse.extract_tags(text, topK=topK)
            return keywords
        except:
            return []


def build_triples(df):
    """
    构建三元组 (head, relation, tail)
    实体类型: 电影, 导演, 演员, 类型, 国家, 年份
    关系类型: 执导, 主演, 属于类型, 制片国家, 上映年份, 描述包含关键词
    """
    print("  [三元组] 构建知识三元组...")
    triples = []
    
    for _, row in df.iterrows():
        movie = row["title"]
        director = row["director"]
        year = str(int(row["year"])) if row["year"] > 0 else "未知"
        rating = row["rating"]
        country = row["country"]
        
        # 三元组1: (电影) - [执导] -> (导演)
        triples.append({
            "head": movie, "head_type": "电影",
            "relation": "执导",
            "tail": director, "tail_type": "导演",
            "movie_id": row.get("id", "")
        })
        
        # 三元组2: (电影) - [上映年份] -> (年份)
        if year != "0" and year != "未知":
            triples.append({
                "head": movie, "head_type": "电影",
                "relation": "上映年份",
                "tail": year + "年", "tail_type": "年份",
                "movie_id": row.get("id", "")
            })
        
        # 三元组3: (电影) - [制片国家] -> (国家)
        if country and country != "未知":
            triples.append({
                "head": movie, "head_type": "电影",
                "relation": "制片国家",
                "tail": country, "tail_type": "国家",
                "movie_id": row.get("id", "")
            })
        
        # 三元组4: (电影) - [评分] -> (评分值)
        if rating > 0:
            triples.append({
                "head": movie, "head_type": "电影",
                "relation": "评分",
                "tail": f"{rating:.1f}分", "tail_type": "评分值",
                "movie_id": row.get("id", "")
            })
        
        # 三元组5~N: (电影) - [主演] -> (演员)
        actors = row.get("actors", [])
        if isinstance(actors, list):
            for actor in actors:
                if actor and str(actor).strip():
                    triples.append({
                        "head": movie, "head_type": "电影",
                        "relation": "主演",
                        "tail": str(actor).strip(), "tail_type": "演员",
                        "movie_id": row.get("id", "")
                    })
        
        # 三元组6~N: (电影) - [属于类型] -> (类型)
        genres = row.get("genres", [])
        if isinstance(genres, list):
            for genre in genres:
                if genre and str(genre).strip():
                    triples.append({
                        "head": movie, "head_type": "电影",
                        "relation": "属于类型",
                        "tail": str(genre).strip(), "tail_type": "类型",
                        "movie_id": row.get("id", "")
                    })
        
        # 三元组7~N: (电影) - [描述关键词] -> (关键词)  -- 使用jieba
        desc = row.get("description", "")
        if desc:
            keywords = extract_keywords(desc, topK=3)
            for kw in keywords:
                if kw and kw.strip():
                    triples.append({
                        "head": movie, "head_type": "电影",
                        "relation": "描述关键词",
                        "tail": kw.strip(), "tail_type": "关键词",
                        "movie_id": row.get("id", "")
                    })
    
    df_triples = pd.DataFrame(triples)
    print(f"  ✓ 共构建 {len(df_triples)} 条三元组")
    return df_triples


def generate_statistics(df, df_triples):
    """生成数据统计信息"""
    stats = {}
    
    # 电影统计
    stats["total_movies"] = len(df)
    stats["avg_rating"] = round(df["rating"].mean(), 2)
    stats["year_range"] = f"{int(df['year'].min())} - {int(df['year'].max())}"
    
    # 实体统计
    entities = {}
    entities["电影"] = len(df)
    entities["导演"] = df["director"].nunique()
    entities["国家"] = df["country"].nunique()
    
    all_actors = set()
    for actors in df["actors"]:
        if isinstance(actors, list):
            for a in actors:
                if a and str(a).strip():
                    all_actors.add(str(a).strip())
    entities["演员"] = len(all_actors)
    
    all_genres = set()
    for genres in df["genres"]:
        if isinstance(genres, list):
            for g in genres:
                if g and str(g).strip():
                    all_genres.add(str(g).strip())
    entities["类型"] = len(all_genres)
    
    stats["entities"] = entities
    stats["total_entities"] = sum(entities.values())
    
    # 关系统计
    relation_counts = df_triples["relation"].value_counts().to_dict()
    stats["relations"] = relation_counts
    stats["total_triples"] = len(df_triples)
    stats["total_relations"] = df_triples["relation"].nunique()
    
    return stats


def preprocess():
    """主流程"""
    print_section("第2步：数据预处理 + 三元组构建")
    
    df_raw = load_csv_data("movies_raw.csv")
    if df_raw is None:
        print("  从样例数据加载...")
        df_raw = load_sample_data()
    else:
        print(f"  从CSV加载 ({len(df_raw)} 条)")
    
    df_clean = clean_data(df_raw)
    save_csv_data(df_clean, "movies_cleaned.csv")
    
    print("  提取描述关键词...")
    df_clean = df_clean.copy()
    df_clean["keywords"] = ""
    for idx, row in df_clean.iterrows():
        desc = row.get("description", "")
        if desc:
            kws = extract_keywords(desc)
            df_clean.at[idx, "keywords"] = ",".join(kws) if kws else ""
    
    save_csv_data(df_clean, "movies_with_keywords.csv")
    
    df_triples = build_triples(df_clean)
    save_csv_data(df_triples, "triples.csv")
    
    stats = generate_statistics(df_clean, df_triples)
    save_json_data(stats, "statistics.json")
    
    print(f"  数据统计:")
    print(f"    电影总数: {stats['total_movies']}")
    print(f"    总实体数: {stats['total_entities']}")
    print(f"    总三元组: {stats['total_triples']}")
    print(f"    关系类型: {stats['total_relations']} 种")
    print(f"    平均评分: {stats['avg_rating']}")
    
    print(f"  预处理完成！")
    return df_clean, df_triples, stats


if __name__ == "__main__":
    df, triples, stats = preprocess()
    
    print("\n三元组示例 (前10条):")
    print(triples.head(10).to_string())
    
    print("\n各关系类型分布:")
    print(triples["relation"].value_counts().to_string())
