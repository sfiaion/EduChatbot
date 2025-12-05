from app.db.neo4j import graph
from ..schemas.gragh import GraphNode, GraphEdge

def get_subgraph(center: str):
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
        center_node = GraphNode(id=n["name"], label=n["name"])
        nodes.append(center_node)
    # 前驱节点
    for p in predecessors:
        if p:
            node = GraphNode(id=p["name"], label=p["name"])
            nodes.append(node)
            edge = GraphEdge(source=p["name"], target=n["name"])
            edges.append(edge)
    # 后继节点
    for s in successors:
        if s:
            node = GraphNode(id=s["name"], label=s["name"])
            nodes.append(node)
            edge = GraphEdge(source=n["name"], target=s["name"])
            edges.append(edge)
    # 去重
    unique_nodes = list({node.id: node for node in nodes}.values())
    return unique_nodes, edges