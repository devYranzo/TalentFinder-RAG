from fastapi import APIRouter
from engine import rag_engine

router = APIRouter(prefix="/system", tags=["Sistema"])

@router.get("/stats")
async def get_stats():
    """Estadísticas globales del sistema y del motor RAG"""
    vector_count = await rag_engine.get_vector_count()
    document_count = await rag_engine.get_indexed_documents_count()
    is_indexed = await rag_engine.is_indexed()
    indexing_status = rag_engine.get_indexing_status()

    return {
        "is_indexed": is_indexed,
        "vectors_count": vector_count,
        "documents_count": document_count,
        "indexing": indexing_status,
        "cache_size": len(rag_engine._query_cache)
    }
