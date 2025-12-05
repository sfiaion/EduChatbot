from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from ..crud.graph import search_knowledge_nodes_by_name

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/search")
def search_knowledge_nodes(
        q: str = Query(...),
        db: Session = Depends(get_db),
):
    return search_knowledge_nodes_by_name(db, q)