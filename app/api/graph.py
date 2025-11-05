# app/api/graph.py
from fastapi import APIRouter, Query
from py2neo import Graph
from app.db.neo4j import graph

router = APIRouter()

@router.get("/knowledge-graph")
def get_knowledge_graph(center: str = Query(..., description="中心节点名称")):
    query = """
    MATCH (n:Knowledge {name: $center})
    OPTIONAL MATCH (p:Knowledge)-[:PREREQUISITE]->(n)
    OPTIONAL MATCH (n)-[:PREREQUISITE]->(s:Knowledge)
    RETURN n, collect(DISTINCT p) AS predecessors, collect(DISTINCT s) AS successors
    """
    record = graph.run(query, center=center).data()
    if not record:
        return {"nodes": [], "edges": []}

    record = record[0]
    n = record["n"]
    predecessors = record["predecessors"]
    successors = record["successors"]
    nodes = []
    edges = []
    # 当前节点
    if n:
        nodes.append({"id": n["name"], "label": n["name"]})
    # 前驱节点
    for p in predecessors:
        if p:
            nodes.append({"id": p["name"], "label": p["name"]})
            edges.append({"from": p["name"], "to": n["name"]})
    # 后继节点
    for s in successors:
        if s:
            nodes.append({"id": s["name"], "label": s["name"]})
            edges.append({"from": n["name"], "to": s["name"]})
    # 去重
    unique_nodes = {node["id"]: node for node in nodes}.values()
    return {"nodes": list(unique_nodes), "edges": edges}
