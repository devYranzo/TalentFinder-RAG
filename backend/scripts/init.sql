-- ===============================================
-- Script de inicialización para LangChain PGVector
-- CORREGIDO: Tipos de datos compatibles con langchain_postgres
-- ===============================================

-- 1. Habilitar la extensión de vectores (requerida por LangChain)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Crear la tabla que usa LangChain automáticamente
-- IMPORTANTE: LangChain usa VARCHAR para los IDs, no UUID
CREATE TABLE IF NOT EXISTS langchain_pg_embedding (
    id VARCHAR PRIMARY KEY,  -- CAMBIADO: VARCHAR en lugar de UUID
    collection_id UUID,
    embedding vector(384), -- 384 es la dimensión de 'multilingual-e5-small'
    document TEXT,
    cmetadata JSONB
);

-- 3. Crear tabla auxiliar para las colecciones
CREATE TABLE IF NOT EXISTS langchain_pg_collection (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR,
    cmetadata JSONB
);

-- 4. Crear índices para optimizar las búsquedas

-- Índice HNSW para búsqueda vectorial ultrarrápida
CREATE INDEX IF NOT EXISTS langchain_pg_embedding_embedding_idx
ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índice para filtrar por colección (muy importante para rendimiento)
CREATE INDEX IF NOT EXISTS langchain_pg_embedding_collection_id_idx
ON langchain_pg_embedding (collection_id);

-- Índice JSONB para búsquedas en metadatos
CREATE INDEX IF NOT EXISTS langchain_pg_embedding_cmetadata_idx
ON langchain_pg_embedding USING gin (cmetadata);

-- 5. Eliminar la tabla antigua si existe (migración)
-- ADVERTENCIA: Esto borrará los datos antiguos. Comentar si quieres migrarlos.
DROP TABLE IF EXISTS cv_vectors;

-- ===============================================
-- Información adicional:
-- ===============================================
-- - La tabla 'langchain_pg_embedding' es creada automáticamente por LangChain
--   pero la creamos aquí para tener control sobre los índices
-- - El campo 'id' es VARCHAR porque LangChain genera IDs como strings
-- - El campo 'collection_id' es un UUID que identifica cada colección
-- - El campo 'cmetadata' almacena metadatos en formato JSON
-- - Los índices mejoran significativamente el rendimiento en búsquedas
-- ===============================================
