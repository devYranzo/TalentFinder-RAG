from fastapi import FastAPI, BackgroundTasks, HTTPException
from app.engine import RAGEngine
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from sqlalchemy import text
from app.database import engine as db_engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RAGEngine()

@app.post("/ingest")
async def start_ingestion(background_tasks: BackgroundTasks):
    """Lanza la indexación de CVs en segundo plano para no bloquear la API."""
    try:
        background_tasks.add_task(engine.index_documents)
        return {"status": "Ingestion started", "message": "The system is processing PDF files."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(q: str):
    try:
        return await engine.query(q)
    except Exception as e:
        print(f"Error detectado: {e}")
        # Al lanzar HTTPException de FastAPI, el middleware de CORS SI funciona
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    try:
        async with db_engine.connect() as conn:
            # LangChain guarda los vectores en la tabla 'langchain_pg_embedding' por defecto
            result = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding"))
            count = result.scalar()
            
        return {
            "is_ready": count > 0,
            "total_vectors": count
        }
    except Exception as e:
        print(f"Error en status: {e}")
        return {"is_ready": False, "total_vectors": 0, "error": str(e)}

if os.path.exists(settings.PDF_PATH):
    app.mount("/pdfs", StaticFiles(directory=settings.PDF_PATH), name="pdfs")