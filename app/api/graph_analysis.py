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
from app.models.user import User
from .deps import get_current_active_teacher

def get_analyzer(
        request: Request,
        class_id: int = Header(..., alias="Class-ID"),
        start_date: str = Header(..., alias="Start-Date"),
        end_date: str = Header(..., alias="End-Date"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_teacher)
) -> KnowledgeGraphAnalyzer:
    try:
        sd = datetime.fromisoformat(start_date)
        ed_raw = datetime.fromisoformat(end_date)
        ed = ed_raw.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    if not is_owned_class(db, class_id, current_user.teacher.id):
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

@router.get("/candidates", response_model=List[str])
def get_candidate_nodes(
        request: Request,
        limit: int = Query(20, description="limit")
):
    analyzer = request.state.analyzer
    sorted_nodes = sorted(analyzer.total_errors.items(), key=lambda x: x[1], reverse=True)
    return [name for name, count in sorted_nodes[:limit]]

# 分析掌握依赖（显示最短/最长前置路径长度，高频前置节点）
@router.get("/node/{name}", response_model=NodeAnalysisResponse)
def get_node_data(
        request: Request,
        name: str = Path(..., description="中心节点名称"),
):
    analyzer = request.state.analyzer
    node = get_knowledge_node_by_name(analyzer.db, name)
    longest_path, preceding_node_names = analyzer.analyze_path_dependency(name)
    if longest_path == -1:
        raise HTTPException(status_code=404, detail=f"知识点 '{name}' 不在知识图谱中")
    # 容错：关系型库没有该节点时，内容置空，错误统计按0与时间区间构造
    content = node.content if node else ""
    total_err = analyzer.total_errors.get(name, 0)
    # 构造完整日期字典
    cur = analyzer.start_date.date()
    end = analyzer.end_date.date()
    daily = {}
    while cur <= end:
        k = str(cur)
        v = (analyzer.daily_errors.get(name) or {}).get(k, 0)
        daily[k] = v
        from datetime import timedelta
        cur = cur + timedelta(days=1)
    return NodeAnalysisResponse(
        node=CenterNode(
            name=name,
            total_errors=total_err,
            daily_errors=daily,
            content=content,
            longest_path=longest_path
        ),
        preceding_nodes=[
            PrecedingNode(
                name=n,
                total_errors=analyzer.total_errors.get(n, 0)
            )
            for n in preceding_node_names
        ]
    )
