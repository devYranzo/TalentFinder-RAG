from fastapi import FastAPI, BackgroundTasks, HTTPException
from app.engine import RAGEngine
from app.config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

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

@app.post("/ingest")
async def start_ingestion(background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(rag_engine.index_documents)
        return {"status": "Ingestion started", "message": "The system is processing PDF files."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(q: str):
    try:
        return await rag_engine.query(q)
    except Exception as e:
        print(f"Error detectado: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    count = await rag_engine.get_vector_count()
    
    total_files = 0
    path_a_contar = settings.PDF_PATH 
    
    if os.path.exists(path_a_contar):
        for root, dirs, files in os.walk(path_a_contar):
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            total_files += len(pdf_files)
    
    return {
        "is_ready": count > 0,
        "total_vectors": count,
        "total_files": total_files,
        "is_indexing": rag_engine.is_indexing,
        "processed_documents": rag_engine.processed_documents,
        "total_documents": rag_engine.total_documents
    }