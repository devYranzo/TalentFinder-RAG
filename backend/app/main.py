from fastapi import FastAPI
from app.engine import RAGEngine
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montamos la carpeta de PDFs para que el frontend pueda abrirlos
# Asegúrate de que settings.PDF_PATH sea la ruta correcta (ej: /app/CVs)
app.mount("/pdfs", StaticFiles(directory=settings.PDF_PATH), name="pdfs")

# Instanciamos tu motor de búsqueda
rag_engine = RAGEngine()

@app.post("/index/start")
async def start_indexing():
    """Inicia la indexación en background sin bloquear"""
    return rag_engine.start_indexing_background()

@app.get("/index/status")
async def get_indexing_status():
    """Obtiene el estado de la indexación en progreso"""
    return rag_engine.get_indexing_status()

@app.post("/index/reindex")
async def reindex_all():
    """Elimina todo y reindexa desde cero"""
    return await rag_engine.reindex_all_documents()

# ============================================
# ENDPOINT PARA CONSULTAS (OPTIMIZADO)
# ============================================

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query_rag(request: QueryRequest):
    """Consulta optimizada al RAG con cache"""
    return await rag_engine.query(request.question)

@app.get("/stats")
async def get_stats():
    """Estadísticas del sistema"""
    vector_count = await rag_engine.get_vector_count()
    indexing_status = rag_engine.get_indexing_status()

    return {
        "vectors_count": vector_count,
        "indexing": indexing_status,
        "cache_size": len(rag_engine._query_cache)
    }

@app.post("/cache/clear")
async def clear_cache():
    """Limpia la cache de consultas"""
    rag_engine.clear_cache()
    return {"status": "cache_cleared"}
