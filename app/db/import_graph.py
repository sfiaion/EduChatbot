from py2neo import Graph, Node, Relationship, NodeMatcher
import sys
import pathlib
import pandas as pd
from app.db.neo4j import graph

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

NAME_EXCEL_PATH = PROJECT_ROOT / "docs" / "知识点.xlsx"
NAME_SHEET_NAME = "Sheet1"

RELATION_EXCEL_PATH = PROJECT_ROOT / "docs" / "知识图谱前后继关系.xlsx"
RELATION_SHEET_NAME = "Sheet1"

df_name = pd.read_excel(NAME_EXCEL_PATH, sheet_name=NAME_SHEET_NAME, dtype=str)
df_name = df_name.dropna(how='all')
df_name = df_name.fillna("")
df_relation = pd.read_excel(RELATION_EXCEL_PATH, sheet_name=RELATION_SHEET_NAME, dtype=str)
df_relation = df_relation.dropna(how='all')
df_relation = df_relation.fillna("")

graph.delete_all()
knowledges = df_name["name"].tolist()
tx = graph.begin()
for name in knowledges:
    name_clean = str(name).strip()
    if name_clean:  # 确保非空
        tx.create(Node("Knowledge", name=name_clean))
graph.commit(tx)
relations = [
    (src, tgt)
    for src, tgt in zip(df_relation["前驱"], df_relation["后继"])
    if src and tgt  # 排除空字符串
]
matcher = NodeMatcher(graph)
tx = graph.begin()
for src, tgt in relations:
    src_node = matcher.match("Knowledge", name=src).first()
    tgt_node = matcher.match("Knowledge", name=tgt).first()
    if src_node and tgt_node:
        tx.create(Relationship(src_node, "PREREQUISITE", tgt_node))
    else:
        raise ValueError(f"节点未找到: 前驱='{src}' 或 后继='{tgt}'")
graph.commit(tx)

print(f"✅ 成功创建 {len(knowledges)} 个节点 和 {len(relations)} 条关系")