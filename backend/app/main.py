from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings
from routes import index, search, system, admin

app = FastAPI(title="TalentFinder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount PDFs
app.mount("/pdfs", StaticFiles(directory=settings.PDF_PATH), name="pdfs")

# Routes
app.include_router(index.router)
app.include_router(search.router)
app.include_router(system.router)
# app.include_router(admin.router)
