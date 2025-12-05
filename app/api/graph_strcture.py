from fastapi import APIRouter, Query, Depends
from fontTools.misc.plistlib import end_date
from app.db.neo4j import graph
from ..schemas.gragh import KnowledgeGraphResponse
from ..services.graph_structure import get_subgraph

router = APIRouter(prefix="/knowledge-graph", tags=["KnowledgeGraph"])

@router.get("")
def get_knowledge_graph(center: str = Query(..., description="中心节点名称")):
    unique_nodes, edges = get_subgraph(center)
    return KnowledgeGraphResponse(nodes=unique_nodes, edges=edges)