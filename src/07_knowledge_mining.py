"""
第7步：知识挖掘分析
1. 演员合作网络分析（中心度分析 + 社区发现）
2. 电影推荐（基于路径的相似度）
3. 电影类型关联挖掘（Apriori关联规则）
4. 图中心度分析（PageRank、Betweenness等）
输出：挖掘分析报告和图表
"""
import sys
sys.path.insert(0, str(__file__).replace("07_knowledge_mining.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from itertools import combinations

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_graph():
    """加载已构建的图"""
    graphml_path = OUTPUT_DIR / "movie_knowledge_graph.graphml"
    if graphml_path.exists():
        G = nx.read_graphml(str(graphml_path))
        return G
    return None


def analyze_actor_collaboration(G):
    """分析1：演员合作网络分析"""
    print("  分析1: 演员合作网络分析...")
    
    actor_movies = defaultdict(set)
    movie_actors = defaultdict(set)
    
    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "")
        if rel == "主演":
            actor = v
            movie = u
        elif rel == "出演":
            actor = v
            movie = u
        else:
            continue
        
        if G.nodes.get(actor, {}).get("type") == "演员":
            actor_movies[actor].add(movie)
            movie_actors[movie].add(actor)
    
    for u, v, data in G.in_edges(data=True):
        rel = data.get("relation", "")
        if rel == "主演":
            actor = u
            movie = v
        else:
            continue
        
        if G.nodes.get(actor, {}).get("type") == "演员":
            actor_movies[actor].add(movie)
            movie_actors[movie].add(actor)
    
    collab_graph = nx.Graph()
    for movie, actors in movie_actors.items():
        actors_list = list(actors)
        for a1, a2 in combinations(actors_list, 2):
            if collab_graph.has_edge(a1, a2):
                collab_graph[a1][a2]["weight"] += 1
                collab_graph[a1][a2]["movies"].append(movie)
            else:
                collab_graph.add_edge(a1, a2, weight=1, movies=[movie])
    
    for actor in actor_movies:
        if actor not in collab_graph:
            collab_graph.add_node(actor)
    
    collab_pairs = []
    for u, v, data in collab_graph.edges(data=True):
        weight = data.get("weight", 1)
        movies = data.get("movies", [])
        collab_pairs.append((u, v, weight, movies))
    
    collab_pairs.sort(key=lambda x: -x[2])
    
    print(f"  合作网络: {collab_graph.number_of_nodes()} 节点, {collab_graph.number_of_edges()} 条合作边")
    
    collab_copy = nx.Graph(collab_graph)
    for u, v, data in collab_copy.edges(data=True):
        if "movies" in data and isinstance(data["movies"], list):
            data["movies"] = ", ".join(data["movies"])
    collab_gexf = MINING_RESULTS_DIR / "actor_collaboration.gexf"
    nx.write_gexf(collab_copy, str(collab_gexf))
    
    return collab_pairs


def analyze_centrality(G):
    """分析2：图中心度分析"""
    print("  分析2: 图中心度分析...")
    
    deg_centrality = nx.degree_centrality(G)
    
    try:
        if G.number_of_nodes() > 500:
            top_nodes = sorted(G.degree(), key=lambda x: -x[1])[:500]
            sub_nodes = [n for n, _ in top_nodes]
            sub_G = G.subgraph(sub_nodes)
        else:
            sub_G = G
        
        betweenness = nx.betweenness_centrality(sub_G, k=min(100, sub_G.number_of_nodes()),
                                                  normalized=True, seed=42)
    except:
        betweenness = {}
    
    try:
        pagerank = nx.pagerank(G)
    except:
        pagerank = {}
    
    results = []
    for node in G.nodes():
        ntype = G.nodes[node].get("type", "未知")
        deg = deg_centrality.get(node, 0)
        btwn = betweenness.get(node, 0) if node in betweenness else 0
        pr = pagerank.get(node, 0)
        results.append({
            "entity": node,
            "type": ntype,
            "degree_centrality": round(deg, 4),
            "betweenness": round(btwn, 4),
            "pagerank": round(pr, 6),
        })
    
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values("pagerank", ascending=False)
    
    save_csv_data(df_results, "centrality_analysis.csv", subdir="processed")
    
    return df_results


def analyze_genre_association(G):
    """分析3：电影类型关联挖掘"""
    print("  分析3: 电影类型关联挖掘...")
    
    movie_genres = {}
    for u, v, data in G.edges(data=True):
        if data.get("relation") == "属于类型":
            movie = u
            genre = v
            if movie not in movie_genres:
                movie_genres[movie] = set()
            movie_genres[movie].add(genre)
    
    co_occurrence = defaultdict(int)
    
    for movie, genres in movie_genres.items():
        genres_list = list(genres)
        for g1, g2 in combinations(genres_list, 2):
            pair = tuple(sorted([g1, g2]))
            co_occurrence[pair] += 1
    
    print(f"  共分析 {len(movie_genres)} 部电影的类型组合")
    
    return movie_genres, co_occurrence


def build_recommendation_system(G):
    """
    分析4：基于知识图谱的电影推荐
    使用路径相似度方法：
    - 基于导演相似度
    - 基于演员相似度
    - 基于类型相似度
    """
    print("\n  [分析4] 电影推荐系统...")
    
    movies = [n for n, d in G.nodes(data=True) if d.get("type") == "电影"]
    print(f"  ✓ 共 {len(movies)} 部电影可推荐")
    
    # 构建电影特征
    movie_features = {}
    for movie in movies:
        features = {"directors": set(), "actors": set(), "genres": set()}
        
        for _, v, data in G.edges(movie, data=True):
            rel = data.get("relation", "")
            if rel == "执导":
                features["directors"].add(v)
            elif rel == "主演":
                features["actors"].add(v)
            elif rel == "属于类型":
                features["genres"].add(v)
        
        movie_features[movie] = features
    
    def recommend(movie_name, top_n=5):
        """为给定电影推荐相似电影"""
        if movie_name not in movie_features:
            return []
        
        target = movie_features[movie_name]
        scores = []
        
        for other_movie, features in movie_features.items():
            if other_movie == movie_name:
                continue
            
            score = 0
            # 导演相似度（权重高）
            if target["directors"] and features["directors"]:
                overlap = len(target["directors"] & features["directors"])
                score += overlap * 3  # 导演匹配权重高
            
            # 类型相似度
            if target["genres"] and features["genres"]:
                overlap = len(target["genres"] & features["genres"])
                score += overlap * 2  # 类型匹配权重中
            
            # 演员相似度
            if target["actors"] and features["actors"]:
                overlap = len(target["actors"] & features["actors"])
                score += overlap * 1  # 演员匹配权重低
            
            if score > 0:
                scores.append((other_movie, score))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_n]
    
    test_movies = ["The Shawshank Redemption", "Inception", "The Dark Knight", "Avatar"]
    for movie in test_movies:
        recs = recommend(movie, top_n=5)
        rec_names = [f"{rec}({score})" for rec, score in recs]
        if rec_names:
            print(f"  推荐 (基于{movie}): {', '.join(rec_names[:3])}")
    
    return recommend


def plot_collaboration_network(collab_pairs, output_path):
    """可视化合作网络"""
    if not collab_pairs:
        return
    
    # 取Top 20合作对
    top_pairs = collab_pairs[:20]
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 创建简单的条形图
    labels = [f"{a} × {b}" for a, b, _, _ in top_pairs]
    values = [w for _, _, w, _ in top_pairs]
    
    # 如果标签太长，截断
    labels = [l[:20] + "..." if len(l) > 20 else l for l in labels]
    
    bars = ax.barh(range(len(labels)), values, color="mediumpurple", alpha=0.8)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("合作次数", fontsize=12)
    ax.set_title("演员合作频次 Top 20", fontsize=14)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis="x")
    
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                str(val), va="center", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 合作网络: {output_path}")


def plot_genre_association_heatmap(movie_genres, output_path):
    """生成类型关联热力图"""
    if not movie_genres:
        return
    
    # 构建共现矩阵
    all_genres = set()
    for genres in movie_genres.values():
        all_genres.update(genres)
    
    all_genres = sorted(all_genres)
    n = len(all_genres)
    co_matrix = defaultdict(lambda: defaultdict(int))
    
    for genres in movie_genres.values():
        genres_list = list(genres)
        for g1, g2 in combinations(genres_list, 2):
            co_matrix[g1][g2] += 1
            co_matrix[g2][g1] += 1
    
    # 只显示出现频率较高的类型
    genre_freq = Counter()
    for genres in movie_genres.values():
        for g in genres:
            genre_freq[g] += 1
    
    top_genres = [g for g, _ in genre_freq.most_common(10)]
    
    # 构建矩阵
    matrix = []
    for g1 in top_genres:
        row = []
        for g2 in top_genres:
            row.append(co_matrix[g1][g2])
        matrix.append(row)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
    
    ax.set_xticks(range(len(top_genres)))
    ax.set_yticks(range(len(top_genres)))
    ax.set_xticklabels(top_genres, fontsize=9, rotation=45)
    ax.set_yticklabels(top_genres, fontsize=9)
    ax.set_title("电影类型共现热力图", fontsize=14)
    
    # 添加数值标签
    for i in range(len(top_genres)):
        for j in range(len(top_genres)):
            if matrix[i][j] > 0:
                ax.text(j, i, str(matrix[i][j]), ha="center", va="center", fontsize=8)
    
    plt.colorbar(im, label="共现次数")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 类型关联热力图: {output_path}")


def mine():
    """主流程"""
    print_section("第7步：知识挖掘分析")
    
    G = load_graph()
    if G is None:
        print("  未找到图数据，请先运行第5步")
        return
    
    collab_pairs = analyze_actor_collaboration(G)
    centrality = analyze_centrality(G)
    movie_genres, co_occurrence = analyze_genre_association(G)
    recommend_fn = build_recommendation_system(G)
    
    plot_collaboration_network(collab_pairs,
                                str(MINING_RESULTS_DIR / "actor_collaboration.png"))
    plot_genre_association_heatmap(movie_genres,
                                    str(MINING_RESULTS_DIR / "genre_association_heatmap.png"))
    
    report_lines = []
    report_lines.append("# 电影知识图谱挖掘分析报告\n")
    
    report_lines.append("## 1. 演员合作网络\n")
    report_lines.append(f"共发现 {len(collab_pairs)} 对合作关系\n")
    report_lines.append("### Top 10 合作组合\n")
    report_lines.append("| 排名 | 演员1 | 演员2 | 合作次数 | 合作电影 |")
    report_lines.append("|------|-------|-------|---------|---------|")
    for i, (a1, a2, w, movies) in enumerate(collab_pairs[:10], 1):
        movie_str = ", ".join(movies[:3])
        report_lines.append(f"| {i} | {a1} | {a2} | {w} | {movie_str} |")
    
    report_lines.append("\n## 2. 图中心度分析\n")
    report_lines.append("### PageRank Top 10\n")
    report_lines.append("| 排名 | 实体 | 类型 | PageRank | 度数中心度 |")
    report_lines.append("|------|------|------|----------|-----------|")
    for i, (_, row) in enumerate(centrality.head(10).iterrows(), 1):
        report_lines.append(f"| {i} | {row['entity']} | {row['type']} | {row['pagerank']} | {row['degree_centrality']} |")
    
    report_lines.append("\n## 3. 电影类型关联\n")
    report_lines.append("### Top 10 频繁共现类型对\n")
    report_lines.append("| 排名 | 类型1 | 类型2 | 共现次数 | 支持度 |")
    report_lines.append("|------|-------|-------|---------|-------|")
    sorted_pairs = sorted(co_occurrence.items(), key=lambda x: -x[1])
    total_movies = len(movie_genres)
    for i, ((g1, g2), cnt) in enumerate(sorted_pairs[:10], 1):
        support = cnt / total_movies if total_movies else 0
        report_lines.append(f"| {i} | {g1} | {g2} | {cnt} | {support:.1%} |")
    
    report_lines.append("\n## 4. 电影推荐\n")
    test_movies = ["The Shawshank Redemption", "Inception", "The Dark Knight", "Avatar"]
    for movie in test_movies:
        recs = recommend_fn(movie, top_n=5)
        report_lines.append(f"### 基于《{movie}》的推荐\n")
        if recs:
            report_lines.append("| 排名 | 推荐电影 | 相似度得分 |")
            report_lines.append("|------|---------|-----------|")
            for i, (rec, score) in enumerate(recs, 1):
                report_lines.append(f"| {i} | {rec} | {score} |")
        report_lines.append("")
    
    report_path = MINING_RESULTS_DIR / "mining_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"  挖掘报告: {report_path}")
    
    print(f"  知识挖掘分析完成！")


if __name__ == "__main__":
    mine()
