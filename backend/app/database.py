from sqlalchemy.ext.asyncio import create_async_engine
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from .config import settings

engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))

embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)

def get_vector_store():
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.COLLECTION_NAME,
        connection=settings.DATABASE_URL,
        use_jsonb=True,
    )