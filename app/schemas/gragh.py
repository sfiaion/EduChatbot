from pydantic import BaseModel
from typing import List, Dict

class GraphNode(BaseModel):
    id: str
    label: str

class GraphEdge(BaseModel):
    source: str
    target: str

class KnowledgeGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class BreakpointResponse(BaseModel):
    name: str
    diff: int  # 当前错误数 - 最大前驱错误数

class CenterNode(BaseModel):
    name: str
    total_errors: int
    daily_errors: Dict[str, int]
    content: str
    longest_path: int

class PrecedingNode(BaseModel):
    name: str
    total_errors: int

class NodeAnalysisResponse(BaseModel):
    node: CenterNode
    preceding_nodes: List[PrecedingNode]