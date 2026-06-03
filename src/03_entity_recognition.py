"""
第3步：实体识别
- 从文本数据中识别命名实体（电影名、人名、组织名等）
- 使用 spaCy 进行实体识别（如果可用）
- 使用基于规则的方法作为备选（基于词典匹配）
- 输出：标注了实体的数据
"""
import sys
sys.path.insert(0, str(__file__).replace("03_entity_recognition.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import re


def try_spacy_ner(texts):
    """
    尝试使用 spaCy 进行实体识别
    如果 spaCy 不可用或未安装中文模型，返回 None
    """
    try:
        import spacy
        # 尝试加载中文模型
        try:
            nlp = spacy.load("zh_core_web_sm")
        except:
            try:
                nlp = spacy.load("zh_core_web_md")
            except:
                print("  [spaCy] 未安装中文模型，跳过...")
                return None
        
        print("  [spaCy] 使用 spaCy 进行实体识别...")
        results = []
        for text in texts:
            if not text or not isinstance(text, str):
                results.append([])
                continue
            doc = nlp(text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            results.append(entities)
        return results
    
    except ImportError:
        print("  [spaCy] spaCy 未安装，使用规则匹配替代...")
        return None
    except Exception as e:
        print(f"  [spaCy] 加载失败: {e}，使用规则匹配替代...")
        return None


def rule_based_ner(text, known_entities):
    """
    基于规则的实体识别
    通过已知实体词典匹配文本中的实体
    """
    if not text or not isinstance(text, str):
        return []
    
    found = []
    for entity_type, entity_list in known_entities.items():
        for entity in entity_list:
            if entity and entity in text:
                found.append((entity, entity_type))
    
    return found


def build_entity_dictionary(df):
    """从结构化数据中构建已知实体词典"""
    print("  [词典] 从结构化数据构建实体词典...")
    
    entities = {
        "电影": [],
        "导演": [],
        "演员": [],
        "类型": [],
        "国家": [],
    }
    
    # 收集电影名
    entities["电影"] = df["title"].dropna().unique().tolist()
    
    # 收集导演
    entities["导演"] = df["director"].dropna().unique().tolist()
    
    # 收集演员
    all_actors = set()
    for actors in df["actors"]:
        if isinstance(actors, list):
            for a in actors:
                if a and str(a).strip():
                    all_actors.add(str(a).strip())
    entities["演员"] = list(all_actors)
    
    # 收集类型
    all_genres = set()
    for genres in df["genres"]:
        if isinstance(genres, list):
            for g in genres:
                if g and str(g).strip():
                    all_genres.add(str(g).strip())
    entities["类型"] = list(all_genres)
    
    # 收集国家
    entities["国家"] = df["country"].dropna().unique().tolist()
    
    # 打印统计
    for k, v in entities.items():
        print(f"    - {k}: {len(v)} 个实体")
    
    return entities


def recognize_entities():
    """主流程"""
    print_section("第3步：实体识别")
    
    df = load_csv_data("movies_cleaned.csv")
    if df is None:
        print("  从样例数据加载...")
        df = load_sample_data()
    else:
        print(f"  加载 {len(df)} 条记录")
    
    import ast
    def parse_list_field(val):
        if isinstance(val, str):
            if val.startswith("["):
                try:
                    return ast.literal_eval(val)
                except:
                    return [val]
            return [x.strip() for x in val.split(",")]
        return val if isinstance(val, list) else []
    
    if "actors" in df.columns and isinstance(df["actors"].iloc[0], str):
        df["actors"] = df["actors"].apply(parse_list_field)
    if "genres" in df.columns and isinstance(df["genres"].iloc[0], str):
        df["genres"] = df["genres"].apply(parse_list_field)
    
    entity_dict = build_entity_dictionary(df)
    
    descriptions = df["description"].fillna("").tolist()
    spacy_results = try_spacy_ner(descriptions)
    
    ner_results = []
    for desc in descriptions:
        found = rule_based_ner(desc, entity_dict)
        ner_results.append(found)
    
    if spacy_results:
        combined_results = []
        for i, (sr, rr) in enumerate(zip(spacy_results, ner_results)):
            combined = list(set(sr + rr))
            combined_results.append(combined)
        ner_results = combined_results
    
    df["recognized_entities"] = [str(r) for r in ner_results]
    
    total_entities_found = sum(len(r) for r in ner_results)
    print(f"  共识别 {total_entities_found} 个实体")
    
    save_csv_data(df, "movies_with_entities.csv")
    
    print(f"  实体识别完成！")
    return df, entity_dict


if __name__ == "__main__":
    df, entity_dict = recognize_entities()
