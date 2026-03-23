import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Recruitment RAG API"
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    DATABASE_URL: str = "postgresql+psycopg://myuser:mypassword@db:5432/rag_db"
    COLLECTION_NAME: str = "cv_vectors"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    PDF_PATH: str = "./CVs"

settings = Settings()