from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from ..crud.graph import search_knowledge_nodes_by_name, list_all_knowledge_nodes

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/search")
def search_knowledge_nodes(
        q: str = Query(...),
        db: Session = Depends(get_db),
):
    return search_knowledge_nodes_by_name(db, q)

@router.get("/all")
def list_knowledge_nodes(
        limit: int = Query(500, ge=1, le=5000),
        db: Session = Depends(get_db),
):
    return list_all_knowledge_nodes(db, limit)
