-- Habilitar la extensión de vectores
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear la tabla si no existe
CREATE TABLE IF NOT EXISTS cv_vectors (
    id uuid PRIMARY KEY,
    embedding vector(384), -- 384 es la dimensión de 'multilingual-e5-small'
    document text,
    metadata jsonb
);

-- Crear el índice HNSW para búsqueda ultrarrápida
-- Solo se crea si no existe para evitar errores en reinicios
CREATE INDEX IF NOT EXISTS idx_cv_vectors_embedding_hnsw
ON cv_vectors USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);