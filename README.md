# 🎬 中文电影知识图谱构建与挖掘

> 《大数据原理与技术》结课项目 · 知识图谱的构建与挖掘

---

## 📋 项目概述

本项目参考课程讲义《第三章 知识图谱构建与挖掘实践》中"专利知识图谱"的技术路线，设计并实现了一个面向**电影领域**的知识图谱构建与挖掘系统。项目覆盖从数据采集、预处理、实体识别、关系抽取、知识存储、可视化查询到知识挖掘的**完整Pipeline**。

采用 **TMDB 5000 Movie Dataset**（Kaggle公开数据集）作为主要数据源，包含 **4,770 部电影**的详细信息。如果TMDB数据不可用，自动回退到内置的100部中文电影样例数据。

## 📊 成果概览

### 使用 TMDB 5000 数据集（实际运行结果）

| 指标 | 数值 |
|------|------|
| **电影节点** | 4,770 部 |
| **总实体数** | 16,564 个（导演2,347 + 演员9,357 + 类型20 + 国家70 + 电影4,770） |
| **关系/三元组** | 65,835 条 |
| **关系类型** | 8 种（执导、主演、属于类型、制片国家、上映年份、评分、描述关键词、提及） |
| **图规模** | 21,186 节点 / 69,620 条边 |
| **演员合作网络** | 44,310 对合作关系 |
| **运行耗时** | ~220 秒（含spaCy NER） |

### 使用内置样例数据（无外部数据时的回退方案）

| 指标 | 数值 |
|------|------|
| **电影节点** | 100 部（中文电影，如《霸王别姬》《功夫》《无间道》等） |
| **总实体数** | 421 个（导演60 + 演员232 + 类型22 + 国家7 + 电影100） |
| **关系/三元组** | 1,331 条 |
| **运行耗时** | ~3 秒 |

## 🏗 系统架构

```
数据采集 (TMDB 5000 CSV / 内置JSON)
    ↓
数据预处理 (Pandas + jieba分词 + 关键词提取)
    ↓
实体识别 (spaCy NER + 词典规则匹配)
    ↓
关系抽取 (正则模板匹配)
    ↓
知识图谱构建 (NetworkX 图 / 可选Neo4j)
    ↓
查询与可视化 (PyEcharts交互图 + Matplotlib统计图)
    ↓
知识挖掘 (合作网络 + 中心度分析 + 类型关联 + 推荐系统)
```

## 🗂 文件结构

```
MovieKG/
├── main.py                          # 主运行脚本（一键运行全部7步）
├── requirements.txt                 # Python依赖
├── data/
│   ├── sample_data/
│   │   └── movie_sample_data.json   # 内置100部电影样例数据
│   ├── raw/                         # 原始数据（TMDB CSV + movies_raw.csv）
│   └── processed/                   # 处理后数据（三元组、实体等）
├── src/
│   ├── utils.py                     # 公共工具函数
│   ├── 01_data_collection.py        # 数据采集
│   ├── 02_data_preprocessing.py     # 数据预处理 + 三元组构建
│   ├── 03_entity_recognition.py     # 实体识别（spaCy + 词典规则）
│   ├── 04_relation_extraction.py    # 关系抽取（正则模板匹配）
│   ├── 05_kg_import.py              # 知识图谱导入（NetworkX + 可选Neo4j）
│   ├── 06_visualization.py          # 查询与可视化（PyEcharts + Matplotlib）
│   └── 07_knowledge_mining.py       # 知识挖掘分析
├── output/
│   ├── visualization/
│   │   ├── kg_visualization.html    # 交互式知识图谱可视化
│   │   ├── kg_network_graph.png     # 静态知识图谱网络图
│   │   ├── rating_distribution.png  # 评分分布图
│   │   ├── genre_distribution.png   # 类型分布图
│   │   ├── year_distribution.png    # 年份分布图
│   │   ├── top_directors.png        # 高产导演Top10
│   │   └── top_actors.png           # 高产演员Top10
│   ├── mining_results/
│   │   ├── mining_report.md         # 知识挖掘分析报告
│   │   ├── actor_collaboration.png  # 演员合作网络图
│   │   ├── actor_collaboration.gexf # 合作网络GEXF文件
│   │   └── genre_association_heatmap.png # 类型关联热力图
│   ├── movie_knowledge_graph.gexf   # 完整知识图谱（Gephi可打开）
│   ├── movie_knowledge_graph.graphml # GraphML格式
│   └── query_results.md             # 查询结果报告
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip

### 安装与运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行项目
cd MovieKG
python main.py
```

### Neo4j 图数据库（可选，用于交互式可视化）

如果已安装 **Neo4j Desktop**，按以下步骤启动：

1. 打开 **Neo4j Desktop**
2. 点击 **"+ Add" → "Local DBMS"** 创建新数据库
3. 设置 **Password** 为 `12345678`（与代码 [`05_kg_import.py:43`](MovieKG/src/05_kg_import.py:43) 中的密码一致），点击 **"Create"**
4. 在数据库卡片上点击 **"Start"**（▶️ 按钮），等待状态变为绿色 **"Running"**
5. 重新运行项目，第5步会自动导入数据到 Neo4j：
   ```bash
   cd MovieKG
   python main.py
   ```
6. 打开浏览器访问 **http://localhost:7474** 查看交互式知识图谱

> 如果未安装 Neo4j，项目默认使用 **NetworkX** 构建图，不影响其他功能。
> 如果设置了不同的密码，需同步修改 [`05_kg_import.py:43`](MovieKG/src/05_kg_import.py:43) 中的 `password` 变量。

### 查看结果

项目运行完成后，查看以下输出文件：

| 文件 | 说明 |
|:----|:------|
| `output/visualization/kg_visualization.html` | 交互式知识图谱可视化（直接浏览器打开） |
| `output/mining_results/mining_report.md` | 知识挖掘分析报告 |
| `output/query_results.md` | 示例查询结果 |
| `output/visualization/*.png` | 统计图表（评分分布、类型分布、年份分布等） |
| `output/movie_knowledge_graph.gexf` | GEXF格式图谱（可用 Gephi 打开） |

### 使用内置样例数据

将 `data/raw/` 目录下的 `tmdb_5000_movies.csv` 和 `tmdb_5000_credits.csv` 移走（或重命名），程序自动使用 `data/sample_data/movie_sample_data.json` 中的100部中文电影数据。

### 可选扩展

- **spaCy 中文模型**：`python -m spacy download zh_core_web_sm`（已安装则跳过）
- **Neo4j 驱动**：`pip install neo4j`（已安装则跳过）
- **TMDB 5000 数据集**：从 Kaggle 下载放入 `data/raw/` 目录

## 🔍 查询示例

### 查询Tom Hanks参演的电影
```
Catch Me If You Can, Philadelphia, The Terminal, Toy Story 2, ...
```

### 查询Steven Spielberg执导的电影
```
Schindler's List, Munich, Amistad, The Terminal, War Horse, ...
```

### 查询电影详细信息（如 The Shawshank Redemption）
```
导演: Frank Darabont
演员: Tim Robbins, Morgan Freeman, ...
类型: Drama, Crime
评分: 8.5分
```

### 基于类型的电影推荐（类似《The Shawshank Redemption》）
```
1. The Dark Knight Rises (类型匹配度: 2)
2. The Dark Knight (类型匹配度: 2)
3. Bound (类型匹配度: 2)
```

## 📈 知识挖掘结果

### 演员合作 Top 5
| 排名 | 演员组合 | 合作次数 |
|------|---------|---------|
| 1 | Owen Wilson × Ben Stiller | 7次 |
| 2 | James Doohan × DeForest Kelley | 7次 |
| 3 | Emma Watson × Rupert Grint | 6次 |
| 4 | Emma Watson × Daniel Radcliffe | 6次 |
| 5 | Rupert Grint × Daniel Radcliffe | 6次 |

### 类型共现 Top 5
| 排名 | 类型组合 | 共现次数 | 支持度 |
|------|---------|---------|-------|
| 1 | Drama × Romance | 601次 | 12.6% |
| 2 | Comedy × Drama | 574次 | 12.1% |
| 3 | Drama × Thriller | 553次 | 11.6% |
| 4 | Action × Thriller | 547次 | 11.5% |
| 5 | Comedy × Romance | 482次 | 10.1% |

### PageRank 中心节点 Top 5
| 排名 | 实体 | 类型 | PageRank |
|------|------|------|----------|
| 1 | United States of America | 国家 | 0.007822 |
| 2 | Drama | 类型 | 0.005709 |
| 3 | Comedy | 类型 | 0.004168 |
| 4 | Thriller | 类型 | 0.003247 |
| 5 | Action | 类型 | 0.002709 |

## 📝 与课程案例对比

| 对比维度 | 课程案例（专利知识图谱） | 本项目（电影知识图谱） |
|---------|----------------------|-------------------|
| 数据规模 | ~1270条专利 | TMDB 5000（4770部电影，16564实体） |
| 实体类型 | 4种 | 6种（电影/导演/演员/类型/国家/关键词） |
| 关系类型 | 4种 | 7种 |
| 技术栈 | Python + Neo4j + jieba + spaCy | Python + NetworkX/Neo4j + jieba + spaCy |
| 核心流程 | 完全一致 | 完全一致 |
| 挖掘分析 | 实体聚类/知识补全 | 合作网络/推荐/关联规则/中心度 |
| 可视化 | Neo4j Browser | PyEcharts交互图/Matplotlib/Gephi |

## 📁 项目文件

所有源文件位于 [`MovieKG/`](MovieKG/) 目录下，核心脚本：
- [`main.py`](MovieKG/main.py) — 一键运行入口
- [`src/02_data_preprocessing.py`](MovieKG/src/02_data_preprocessing.py) — 数据预处理与三元组构建
- [`src/05_kg_import.py`](MovieKG/src/05_kg_import.py) — 知识图谱构建
- [`src/06_visualization.py`](MovieKG/src/06_visualization.py) — 查询与可视化
- [`src/07_knowledge_mining.py`](MovieKG/src/07_knowledge_mining.py) — 知识挖掘分析
