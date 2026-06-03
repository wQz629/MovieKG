"""
第5步：知识图谱导入
支持两种模式：
  Mode A: Neo4j 图数据库（如果已安装Neo4j）
  Mode B: NetworkX 图（纯Python，无需安装数据库）
- 创建节点和关系
- 建立索引
- 输出：可供查询的知识图谱
"""
import sys
sys.path.insert(0, str(__file__).replace("05_kg_import.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import networkx as nx


def try_neo4j_import(triples_df):
    """
    尝试导入 Neo4j
    如果 Neo4j 不可用，返回 False
    
    注意：需要同时满足两个条件：
    1. pip install neo4j (Python驱动)
    2. 运行 Neo4j 数据库服务（需下载安装Neo4j Desktop）
       下载地址: https://neo4j.com/download/
       默认连接: bolt://localhost:7687, 用户名/密码: neo4j/12345678 
    """
    print("\n  [Neo4j] 尝试连接Neo4j数据库...")
    print("  [Neo4j] 需要 Neo4j 数据库服务正在运行 (端口 7687)")
    
    try:
        from neo4j import GraphDatabase
        print("  [Neo4j] Python驱动已安装 ✓")
    except ImportError:
        print("  [Neo4j] Python驱动未安装: pip install neo4j")
        print("  [Neo4j] 切换到NetworkX模式...")
        return False
    
    # Neo4j 连接配置
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "12345678"  
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("  [Neo4j] 数据库连接成功")
        
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            
            # 创建索引
            try:
                session.run("CREATE INDEX movie_name IF NOT EXISTS FOR (m:Movie) ON (m.name)")
                session.run("CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)")
            except:
                pass
            
            # 批量导入
            batch_size = 500
            total = len(triples_df)
            log_interval = 10000
            
            for i in range(0, total, batch_size):
                batch = triples_df.iloc[i:i+batch_size]
                
                for _, row in batch.iterrows():
                    head = row["head"]
                    head_type = row["head_type"]
                    relation = row["relation"]
                    tail = row["tail"]
                    tail_type = row["tail_type"]
                    
                    head_label = map_type_to_label(head_type)
                    tail_label = map_type_to_label(tail_type)
                    
                    cypher = f"""
                    MERGE (h:{head_label} {{name: $head}})
                    MERGE (t:{tail_label} {{name: $tail}})
                    MERGE (h)-[r:{relation}]->(t)
                    """
                    session.run(cypher, head=head, tail=tail)
                
                progress = min(i + batch_size, total)
                if progress % log_interval == 0 or progress == total:
                    print(f"  [Neo4j] 导入进度: {progress}/{total}")
        
        driver.close()
        print(f"  [Neo4j] 导入完成！共 {total} 条关系")
        print(f"  [Neo4j] 打开 http://localhost:7474 查看可视化")
        return True
    
    except Exception as e:
        error_msg = str(e)
        if "ConnectionError" in error_msg or "Failed to establish" in error_msg:
            print("  [Neo4j] 无法连接到数据库服务器（服务未运行）")
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            print("  [Neo4j] 认证失败（请检查密码）")
        else:
            print(f"  [Neo4j] 连接失败")
        
        print("  [Neo4j] 切换到NetworkX模式")
        return False


def map_type_to_label(entity_type):
    """映射实体类型到Neo4j标签"""
    mapping = {
        "电影": "Movie",
        "导演": "Director",
        "演员": "Actor",
        "类型": "Genre",
        "国家": "Country",
        "年份": "Year",
        "评分值": "Rating",
        "关键词": "Keyword",
        "作品": "Work",
    }
    return mapping.get(entity_type, "Entity")


def build_networkx_graph(triples_df):
    """使用 NetworkX 构建图"""
    G = nx.MultiDiGraph()
    
    for _, row in triples_df.iterrows():
        head = str(row["head"])
        tail = str(row["tail"])
        relation = row["relation"]
        head_type = row["head_type"]
        tail_type = row["tail_type"]
        
        G.add_node(head, type=head_type)
        G.add_node(tail, type=tail_type)
        G.add_edge(head, tail, relation=relation)
    
    return G


def save_graph_gexf(G):
    """保存图为GEXF格式"""
    filepath = OUTPUT_DIR / "movie_knowledge_graph.gexf"
    nx.write_gexf(G, str(filepath))
    return filepath


def save_graph_graphml(G):
    """保存图为GraphML格式"""
    filepath = OUTPUT_DIR / "movie_knowledge_graph.graphml"
    nx.write_graphml(G, str(filepath))
    return filepath


def export_node_list(G):
    """导出节点列表"""
    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            "name": node,
            "type": data.get("type", "未知"),
            "degree": G.degree(node)
        })
    
    df_nodes = pd.DataFrame(nodes)
    df_nodes = df_nodes.sort_values("degree", ascending=False)
    save_csv_data(df_nodes, "node_list.csv")
    return df_nodes


def export_edge_list(G):
    """导出边列表"""
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "relation": data.get("relation", "未知"),
            "source_type": G.nodes[u].get("type", "未知"),
            "target_type": G.nodes[v].get("type", "未知")
        })
    
    df_edges = pd.DataFrame(edges)
    save_csv_data(df_edges, "edge_list.csv")
    return df_edges


def kg_import():
    """主流程"""
    print_section("第5步：知识图谱导入")
    
    triples_df = load_csv_data("triples_enriched.csv")
    if triples_df is None:
        triples_df = load_csv_data("triples.csv")
    if triples_df is None:
        print("  未找到三元组数据，请先运行预处理步骤")
        return None
    
    print(f"  加载 {len(triples_df)} 条三元组")
    
    neo4j_success = try_neo4j_import(triples_df)
    
    G = build_networkx_graph(triples_df)
    
    save_graph_gexf(G)
    save_graph_graphml(G)
    
    df_nodes = export_node_list(G)
    df_edges = export_edge_list(G)
    
    print(f"  图谱规模: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
    
    if neo4j_success:
        print(f"  Neo4j可视化: http://localhost:7474")
    
    return G


if __name__ == "__main__":
    G = kg_import()
