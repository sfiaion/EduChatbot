# app/api/graph_analysis.py
from fastapi import APIRouter, Query, Depends, HTTPException, Path, Request, Header
from datetime import datetime
from ..schemas.gragh import BreakpointResponse, NodeAnalysisResponse, CenterNode, PrecedingNode
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from ..services.graph_analysis import KnowledgeGraphAnalyzer
from ..crud.graph import get_knowledge_node_by_name
from ..crud.clazz import is_owned_class

def get_analyzer(
        request: Request,
        class_id: int = Header(..., alias="Class-ID"),
        start_date: str = Header(..., alias="Start-Date"),
        end_date: str = Header(..., alias="End-Date"),
        db: Session = Depends(get_db),
) -> KnowledgeGraphAnalyzer:
    try:
        sd = datetime.fromisoformat(start_date)
        ed = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    if not is_owned_class(db, class_id, 1): # teacher_id暂时写死为1
        raise HTTPException(403, "班级不存在或无权访问")
    analyzer = KnowledgeGraphAnalyzer(db=db, class_id=class_id, start_date=sd, end_date=ed)
    request.state.analyzer = analyzer
    return analyzer

router = APIRouter(prefix="/knowledge-graph", tags=["KnowledgeGraph"], dependencies=[Depends(get_analyzer)])

# 班级异常错误增长点
@router.get("/breakpoints", response_model=List[BreakpointResponse])
def get_class_breakpoints(
        request: Request,
        top_k: int = Query(3, description="返回前k个断点"),
):
    analyzer = request.state.analyzer
    breakpoints = analyzer.find_top_breakpoints_by_name(top_k=top_k)
    return [
        BreakpointResponse(
            name=name,
            diff=diff
        )
        for name, diff in breakpoints
    ]

# 分析掌握依赖（显示最短/最长前置路径长度，高频前置节点）
@router.get("/node/{name}", response_model=NodeAnalysisResponse)
def get_node_data(
        request: Request,
        name: str = Path(..., description="中心节点名称"),
):
    analyzer = request.state.analyzer
    node = get_knowledge_node_by_name(analyzer.db, name)
    if not node:
        raise HTTPException(status_code=404, detail=f"知识点 '{name}' 不存在")
    longest_path, preceding_node_names = analyzer.analyze_path_dependency(name)

    return NodeAnalysisResponse(
        node=CenterNode(
            name=name,
            # 当前节点的总错误次数
            total_errors=analyzer.total_errors.get(name),
            # 当前节点的每日错误，用于折线图
            daily_errors=analyzer.daily_errors.get(name),
            content=node.content,
            # 当前节点的最长前置路径
            longest_path=longest_path
        ),
        # 高频前置节点，以及它们的总错误次数
        preceding_nodes=[
            PrecedingNode(
                name=n,
                total_errors=analyzer.total_errors.get(n)
            )
            for n in preceding_node_names
        ]
    )