from sqlalchemy.ext.asyncio import create_async_engine
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from .config import settings

# Motor asíncrono para operaciones directas en la base de datos
engine = create_async_engine(settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://"))

# Modelo de embeddings
embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

def get_vector_store():
    """
    Retorna una instancia de PGVector.
    PGVector usa automáticamente la tabla 'langchain_pg_embedding'
    y distingue entre colecciones usando el campo 'cmetadata->>'collection_id''
    """
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.COLLECTION_NAME,
        connection=settings.DATABASE_URL,
        use_jsonb=True,
    )
