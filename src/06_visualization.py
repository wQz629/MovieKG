"""
第6步：查询与可视化
- 执行常见的Cypher风格查询（在NetworkX上）
- 生成统计图表（PyEcharts/Matplotlib）
- 输出：可视化HTML文件和统计图表
"""
import sys
sys.path.insert(0, str(__file__).replace("06_visualization.py", "").rstrip("/\\"))

from utils import *
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")  # 非交互式后端
import matplotlib.pyplot as plt
from collections import Counter

# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def load_graph():
    """加载已构建的图"""
    graphml_path = OUTPUT_DIR / "movie_knowledge_graph.graphml"
    if graphml_path.exists():
        G = nx.read_graphml(str(graphml_path))
        return G
    return None


def query_actor_movies(G, actor_name):
    """查询某个演员参演的电影"""
    if actor_name not in G:
        return []
    movies = set()
    for _, v, data in G.edges(actor_name, data=True):
        if data.get("relation") in ["主演", "出演"]:
            movies.add(v)
    # 反向：通过"主演"关系找到的电影
    for u, _, data in G.in_edges(actor_name, data=True):
        if data.get("relation") == "主演":
            movies.add(u)
    return sorted(movies)


def query_director_movies(G, director_name):
    """查询某个导演执导的电影"""
    if director_name not in G:
        return []
    movies = []
    # 导演->电影（执导关系）
    for _, v, data in G.edges(director_name, data=True):
        if data.get("relation") == "执导":
            movies.append(v)
    # 电影->导演（执导关系）
    for u, _, data in G.in_edges(director_name, data=True):
        if data.get("relation") == "执导":
            movies.append(u)
    return list(set(movies))


def query_movie_info(G, movie_name):
    """查询某部电影的完整信息"""
    if movie_name not in G:
        return {}
    info = {"movie": movie_name, "director": [], "actors": [], 
            "genres": [], "country": [], "year": [], "rating": []}
    
    for _, v, data in G.edges(movie_name, data=True):
        rel = data.get("relation", "")
        if rel == "执导":
            info["director"].append(v)
        elif rel == "主演":
            info["actors"].append(v)
        elif rel == "属于类型":
            info["genres"].append(v)
        elif rel == "制片国家":
            info["country"].append(v)
        elif rel == "上映年份":
            info["year"].append(v)
        elif rel == "评分":
            info["rating"].append(v)
    
    return info


def query_collaboration(G, person1, person2):
    """查询两人合作过的电影"""
    if person1 not in G or person2 not in G:
        return []
    # 找出两人都参与的电影
    movies1 = set()
    for u, v, _ in G.edges(person1, data=True):
        if G.nodes[v].get("type") == "电影":
            movies1.add(v)
    for u, v, _ in G.in_edges(person1, data=True):
        if G.nodes[u].get("type") == "电影":
            movies1.add(u)
    
    movies2 = set()
    for u, v, _ in G.edges(person2, data=True):
        if G.nodes[v].get("type") == "电影":
            movies2.add(v)
    for u, v, _ in G.in_edges(person2, data=True):
        if G.nodes[u].get("type") == "电影":
            movies2.add(u)
    
    return list(movies1 & movies2)


def query_recommend_by_genre(G, movie_name, top_n=5):
    """基于类型的电影推荐"""
    info = query_movie_info(G, movie_name)
    if not info:
        return []
    
    target_genres = set(info["genres"])
    if not target_genres:
        return []
    
    # 找出所有电影
    movie_scores = {}
    for node, data in G.nodes(data=True):
        if data.get("type") == "电影" and node != movie_name:
            movie_info = query_movie_info(G, node)
            movie_genres = set(movie_info["genres"])
            if movie_genres:
                # 计算类型重叠度
                overlap = len(target_genres & movie_genres)
                if overlap > 0:
                    movie_scores[node] = overlap
    
    # 排序
    return sorted(movie_scores.items(), key=lambda x: -x[1])[:top_n]


def perform_queries(G):
    """执行示例查询"""
    print("  执行示例查询:")
    
    print("\n  查询1: Tom Hanks 参演的电影:")
    movies = query_actor_movies(G, "Tom Hanks")
    if movies:
        for m in movies[:8]:
            print(f"    - {m}")
    
    print("\n  查询2: Steven Spielberg 执导的电影:")
    movies = query_director_movies(G, "Steven Spielberg")
    if movies:
        for m in movies[:6]:
            print(f"    - {m}")
    
    print("\n  查询3: The Shawshank Redemption 详细信息:")
    info = query_movie_info(G, "The Shawshank Redemption")
    if info:
        for k, v in info.items():
            if v:
                print(f"    - {k}: {', '.join(v) if isinstance(v, list) else v}")
    
    print("\n  查询4: Christopher Nolan × Leonardo DiCaprio 合作电影:")
    collab = query_collaboration(G, "Christopher Nolan", "Leonardo DiCaprio")
    if collab:
        for m in collab:
            print(f"    - {m}")
    else:
        print("    (无直接合作)")
    
    print("\n  查询5: 基于类型推荐 (类似 The Shawshank Redemption):")
    recs = query_recommend_by_genre(G, "The Shawshank Redemption", top_n=5)
    if recs:
        for movie, score in recs:
            print(f"    - {movie} (类型匹配度: {score})")


def plot_rating_distribution(G, output_path):
    """绘制评分分布图"""
    ratings = []
    for node, data in G.nodes(data=True):
        if data.get("type") == "电影":
            info = query_movie_info(G, node)
            if info["rating"]:
                rating_str = info["rating"][0].replace("分", "")
                try:
                    ratings.append(float(rating_str))
                except:
                    pass
    
    if not ratings:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(ratings, bins=20, color="skyblue", edgecolor="black", alpha=0.7)
    ax.set_xlabel("评分", fontsize=12)
    ax.set_ylabel("电影数量", fontsize=12)
    ax.set_title("电影评分分布", fontsize=14)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 评分分布: {output_path}")


def plot_genre_distribution(G, output_path):
    """绘制电影类型分布图"""
    genre_counts = Counter()
    for node, data in G.nodes(data=True):
        if data.get("type") == "类型":
            genre_name = node
            # 统计连接到此类型的电影数
            count = G.degree(node)
            genre_counts[genre_name] = count
    
    if not genre_counts:
        return
    
    # 按数量排序
    sorted_genres = genre_counts.most_common(15)
    genres, counts = zip(*sorted_genres)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(genres)), counts, color="lightcoral")
    ax.set_yticks(range(len(genres)))
    ax.set_yticklabels(genres, fontsize=10)
    ax.set_xlabel("电影数量", fontsize=12)
    ax.set_title("电影类型分布", fontsize=14)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis="x")
    
    # 添加数值标签
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
                str(count), va="center", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 类型分布: {output_path}")


def plot_year_distribution(G, output_path):
    """绘制电影年份分布图"""
    years = []
    for node, data in G.nodes(data=True):
        if data.get("type") == "电影":
            info = query_movie_info(G, node)
            if info["year"]:
                year_str = info["year"][0].replace("年", "")
                try:
                    years.append(int(year_str))
                except:
                    pass
    
    if not years:
        return
    
    year_counter = Counter(years)
    sorted_years = sorted(year_counter.items())
    years_list, counts_list = zip(*sorted_years)
    
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(years_list, counts_list, color="lightgreen", edgecolor="black", alpha=0.7)
    ax.set_xlabel("年份", fontsize=12)
    ax.set_ylabel("电影数量", fontsize=12)
    ax.set_title("电影上映年份分布", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 年份分布: {output_path}")


def plot_top_directors(G, output_path):
    """绘制高产导演图"""
    director_counts = Counter()
    for node, data in G.nodes(data=True):
        if data.get("type") == "导演":
            director_counts[node] = G.degree(node)
    
    if not director_counts:
        return
    
    top_directors = director_counts.most_common(10)
    names, counts = zip(*top_directors)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(names)), counts, color="gold", edgecolor="black", alpha=0.8)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=10, rotation=30)
    ax.set_ylabel("关联电影数", fontsize=12)
    ax.set_title("高产导演 Top 10", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                str(count), ha="center", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 高产导演: {output_path}")


def plot_top_actors(G, output_path):
    """绘制高产演员图"""
    actor_counts = Counter()
    for node, data in G.nodes(data=True):
        if data.get("type") == "演员":
            actor_counts[node] = G.degree(node)
    
    if not actor_counts:
        return
    
    top_actors = actor_counts.most_common(10)
    names, counts = zip(*top_actors)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(names)), counts, color="lightskyblue", edgecolor="black", alpha=0.8)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=10, rotation=30)
    ax.set_ylabel("参演电影数", fontsize=12)
    ax.set_title("高产演员 Top 10", fontsize=14)
    ax.grid(True, alpha=0.3, axis="y")
    
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                str(count), ha="center", fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [图表] 高产演员: {output_path}")


def generate_echarts_html(G, output_path):
    """生成PyEcharts交互式可视化HTML"""
    print("\n  [ECharts] 生成交互式可视化...")
    
    try:
        from pyecharts import options as opts
        from pyecharts.charts import Graph as EGraph
        
        # 准备节点
        nodes = []
        categories = {}
        for node, data in G.nodes(data=True):
            ntype = data.get("type", "未知")
            if ntype not in categories:
                categories[ntype] = len(categories)
            
            # 根据类型设置节点大小
            size = 20 if ntype == "电影" else (15 if ntype in ["导演", "演员"] else 10)
            
            nodes.append({
                "name": node,
                "symbolSize": size,
                "category": categories[ntype],
                "itemStyle": {"opacity": 0.8}
            })
        
        # 准备边
        links = []
        for u, v, data in G.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "value": data.get("relation", ""),
                "lineStyle": {"opacity": 0.4, "width": 1}
            })
        
        # 如果节点太多，进行采样（取度数最高的前30个节点，确保可视化可渲染）
        MAX_NODES = 30
        if len(nodes) > MAX_NODES:
            node_names = set()
            sorted_nodes = sorted(nodes, key=lambda x: G.degree(x["name"]), reverse=True)
            for n in sorted_nodes[:MAX_NODES]:
                node_names.add(n["name"])
            
            nodes = [n for n in nodes if n["name"] in node_names]
            links = [l for l in links if l["source"] in node_names and l["target"] in node_names]
        
        # 创建类别列表
        cat_list = [{"name": name} for name, _ in sorted(categories.items(), key=lambda x: x[1])]
        
        # 创建图表
        graph = (
            EGraph(init_opts=opts.InitOpts(width="1200px", height="800px"))
            .add(
                "",
                nodes=nodes,
                links=links,
                categories=cat_list,
                repulsion=300,
                edge_length=150,
                is_draggable=True,
                is_rotate_label=True,
                gravity=0.3,
                edge_symbol=["none", "arrow"],
                edge_symbol_size=[0, 6],
                linestyle_opts=opts.LineStyleOpts(curve=0.2),
                label_opts=opts.LabelOpts(position="right", font_size=10),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="电影知识图谱可视化"),
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left",
                    pos_top="middle"
                ),
                tooltip_opts=opts.TooltipOpts(
                    formatter="{b}: {c}"
                ),
            )
        )
        
        graph.render(str(output_path))
        
        # 替换CDN为国内可访问的镜像
        with open(output_path, "r", encoding="utf-8") as f:
            html = f.read()
        # 尝试多个CDN源（按优先顺序）
        cdn_fixes = [
            ("https://assets.pyecharts.org/assets/v6/echarts.min.js",
             "https://cdn.bootcdn.net/ajax/libs/echarts/5.6.0/echarts.min.js"),
        ]
        for old_url, new_url in cdn_fixes:
            html = html.replace(old_url, new_url)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"  ✓ ECharts 可视化: {output_path}")
        print(f"  [提示] 如无法渲染，请查看同目录下的 kg_network_graph.png")
        return True
        
    except ImportError:
        print("  [ECharts] pyecharts 未安装，跳过...")
        return False
    except Exception as e:
        print(f"  [ECharts] 生成失败: {e}")
        return False


def generate_network_image(G, output_path):
    """生成NetworkX力导向图（静态PNG，作为ECharts的补充）"""
    print("\n  [Network] 生成静态知识图谱网络图...")
    try:
        # 采样：取度数最高的前50个节点
        top_nodes = sorted(G.degree(), key=lambda x: -x[1])[:50]
        sub_nodes = [n for n, _ in top_nodes]
        sub_G = G.subgraph(sub_nodes)
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # 根据类型分配颜色
        type_colors = {
            "电影": "#FF6B6B", "导演": "#4ECDC4", "演员": "#45B7D1",
            "类型": "#FFA07A", "国家": "#98D8C8", "年份": "#F7DC6F",
            "评分值": "#BB8FCE", "关键词": "#85C1E9",
        }
        
        color_map = []
        for node in sub_G.nodes():
            ntype = sub_G.nodes[node].get("type", "未知")
            color_map.append(type_colors.get(ntype, "#95A5A6"))
        
        # 使用spring layout
        pos = nx.spring_layout(sub_G, k=2, iterations=50, seed=42)
        
        # 绘制节点
        nx.draw_networkx_nodes(sub_G, pos, node_color=color_map,
                               node_size=80, alpha=0.8, ax=ax)
        
        # 绘制边
        nx.draw_networkx_edges(sub_G, pos, alpha=0.15, arrows=False, ax=ax)
        
        # 绘制标签（只显示电影和人物，避免太多）
        labels = {}
        for node in sub_G.nodes():
            ntype = sub_G.nodes[node].get("type", "")
            if ntype in ["电影", "导演", "演员"]:
                labels[node] = node
        
        nx.draw_networkx_labels(sub_G, pos, labels, font_size=6, ax=ax)
        
        ax.set_title("电影知识图谱网络图 (Top 50 节点)", fontsize=14)
        ax.axis("off")
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close()
        print(f"  ✓ 网络图: {output_path}")
        return True
    except Exception as e:
        print(f"  [Network] 生成失败: {e}")
        return False


def visualize():
    """主流程"""
    print_section("第6步：查询与可视化")
    
    G = load_graph()
    if G is None:
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from kg_import import kg_import
            G = kg_import()
        except ImportError as e:
            print(f"  无法导入kg_import: {e}")
        if G is None:
            print("  无法加载图数据")
            return
    
    perform_queries(G)
    
    plot_rating_distribution(G, str(VIZ_DIR / "rating_distribution.png"))
    plot_genre_distribution(G, str(VIZ_DIR / "genre_distribution.png"))
    plot_year_distribution(G, str(VIZ_DIR / "year_distribution.png"))
    plot_top_directors(G, str(VIZ_DIR / "top_directors.png"))
    plot_top_actors(G, str(VIZ_DIR / "top_actors.png"))
    
    generate_echarts_html(G, str(VIZ_DIR / "kg_visualization.html"))
    generate_network_image(G, str(VIZ_DIR / "kg_network_graph.png"))
    
    report = []
    report.append("# 电影知识图谱查询与可视化报告\n")
    report.append(f"## 图谱规模\n")
    report.append(f"- 总节点数: {G.number_of_nodes()}")
    report.append(f"- 总边数: {G.number_of_edges()}\n")
    
    report.append("## 示例查询结果\n")
    report.append("### 查询1: Tom Hanks 参演电影")
    movies = query_actor_movies(G, "Tom Hanks")
    if movies:
        for m in movies[:8]:
            report.append(f"- {m}")
    report.append("")
    
    report.append("### 查询2: Steven Spielberg 执导电影")
    movies = query_director_movies(G, "Steven Spielberg")
    if movies:
        for m in movies[:6]:
            report.append(f"- {m}")
    report.append("")
    
    report.append("### 查询3: 类似 The Shawshank Redemption 的电影推荐")
    recs = query_recommend_by_genre(G, "The Shawshank Redemption", top_n=5)
    if recs:
        for movie, score in recs:
            report.append(f"- {movie} (类型匹配度: {score})")
    
    report_path = OUTPUT_DIR / "query_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"  查询结果报告: {report_path}")
    
    print(f"  查询与可视化完成！")


if __name__ == "__main__":
    visualize()
