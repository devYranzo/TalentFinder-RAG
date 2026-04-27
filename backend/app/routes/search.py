from fastapi import APIRouter
from pydantic import BaseModel
from engine import rag_engine

router = APIRouter(tags=["Buscador"])

class QueryRequest(BaseModel):
    question: str

@router.post("/query")
async def query_rag(request: QueryRequest):
    return await rag_engine.query(request.question)

@router.post("/cache/clear")
async def clear_cache():
    rag_engine.clear_cache()
    return {"status": "cache_cleared"}
