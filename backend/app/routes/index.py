from fastapi import APIRouter
from engine import rag_engine

router = APIRouter(prefix="/index", tags=["Indexación"])

@router.post("/start")
async def start_indexing():
    return rag_engine.start_indexing_background()

@router.get("/status")
async def get_indexing_status():
    return await rag_engine.get_indexing_status_complete()

@router.post("/reindex")
async def reindex_all():
    return await rag_engine.reindex_all_documents()
