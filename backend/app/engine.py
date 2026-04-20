import time
import asyncio
from functools import lru_cache
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text, create_engine

from .config import settings
from .database import get_vector_store

class RAGEngine:
    def __init__(self):
        self.vector_store = get_vector_store()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
            max_retries=6,
            timeout=60
        )
        self.is_indexing = False
        self.processed_documents = 0
        self.total_documents = 0
        self.indexing_error: Optional[str] = None
        # Cache para consultas frecuentes
        self._query_cache = {}
        self._cache_ttl = 300  # 5 minutos

        # Engine síncrono SOLO para operaciones de indexación
        self._sync_engine = None

        # Task de indexación en background
        self._indexing_task: Optional[asyncio.Task] = None

    def _get_sync_engine(self):
        """Lazy loading del engine síncrono"""
        if self._sync_engine is None:
            # Crear versión síncrona de la URL de conexión
            db_url = settings.DATABASE_URL.replace('+asyncpg', '')
            self._sync_engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verificar conexión antes de usar
                pool_recycle=3600    # Reciclar conexiones cada hora
            )
        return self._sync_engine

    def _index_documents_sync(self):
        """Versión síncrona interna de la indexación"""
        self.indexing_error = None

        try:
            loader = DirectoryLoader(
                settings.PDF_PATH,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                recursive=True
            )
            docs = loader.load()

            # Obtener documentos existentes
            existing_ids = set()
            try:
                sync_engine = self._get_sync_engine()
                with sync_engine.connect() as conn:
                    collection_result = conn.execute(
                        text("SELECT uuid FROM langchain_pg_collection WHERE name = :name LIMIT 1"),
                        {"name": settings.COLLECTION_NAME}
                    )
                    collection_uuid = collection_result.scalar()

                    if collection_uuid:
                        result = conn.execute(
                            text("""
                                SELECT DISTINCT cmetadata->>'source' as source
                                FROM langchain_pg_embedding
                                WHERE collection_id = :uuid
                                AND cmetadata->>'source' IS NOT NULL
                            """),
                            {"uuid": collection_uuid}
                        )
                        existing_ids = {row[0] for row in result}
                        print(f"✓ Encontrados {len(existing_ids)} documentos ya indexados")
                    else:
                        print(f"✓ Colección '{settings.COLLECTION_NAME}' vacía o nueva")
            except Exception as e:
                print(f"Aviso: No se pudieron obtener documentos existentes: {e}")

            new_docs = [d for d in docs if d.metadata.get('source') not in existing_ids]

            if not new_docs:
                print("No hay documentos nuevos para indexar.")
                return 0

            self.total_documents = len(new_docs)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = text_splitter.split_documents(new_docs)

            for chunk in chunks:
                chunk.page_content = chunk.page_content.replace("\x00", "")

            print(f"Indexando {len(new_docs)} archivos nuevos ({len(chunks)} chunks)...")

            # ✅ OPTIMIZACIÓN: Lotes más pequeños con pausas adaptativas
            batch_size = 20  # Reducido para mayor estabilidad
            lotes = [chunks[i:i+batch_size] for i in range(0, len(chunks), batch_size)]

            for lote_idx, lote in enumerate(lotes):
                # Verificar si debemos cancelar
                if not self.is_indexing:
                    print("⚠ Indexación cancelada por el usuario")
                    break

                try:
                    self.vector_store.add_documents(lote)

                    # Actualizar progreso
                    self.processed_documents = min(
                        int((lote_idx + 1) * len(lote) / len(chunks) * len(new_docs)),
                        len(new_docs)
                    )
                    print(f"Progreso: {self.processed_documents}/{self.total_documents} documentos ({lote_idx+1}/{len(lotes)} lotes)")

                    # Pausa adaptativa: más corta al principio, más larga si hay muchos lotes
                    if lote_idx < 10:
                        time.sleep(1.5)  # Primeros lotes: pausa corta
                    else:
                        time.sleep(2.5)  # Lotes posteriores: pausa más larga

                except Exception as e:
                    print(f"⚠ Error en lote {lote_idx+1}: {e}")
                    # Pausa más larga si hay error
                    time.sleep(5)
                    continue

            # Limpiar cache después de indexar
            self._query_cache.clear()
            print(f"✓ Indexación completada: {self.processed_documents} documentos procesados")
            return len(chunks)

        except Exception as e:
            error_msg = f"Error crítico durante indexación: {e}"
            print(error_msg)
            self.indexing_error = error_msg
            return 0

    async def index_documents_async(self):
        """Indexación asíncrona en background (no bloqueante)"""
        if self.is_indexing:
            return {"status": "already_running", "processed": self.processed_documents, "total": self.total_documents}

        self.is_indexing = True
        self.processed_documents = 0
        self.total_documents = 0

        try:
            # Ejecutar en thread pool para no bloquear el event loop
            result = await asyncio.to_thread(self._index_documents_sync)
            return {
                "status": "completed",
                "chunks_indexed": result,
                "documents_processed": self.processed_documents,
                "error": self.indexing_error
            }
        finally:
            self.is_indexing = False

    def start_indexing_background(self):
        """Inicia la indexación en background sin bloquear"""
        if self._indexing_task and not self._indexing_task.done():
            return {"status": "already_running", "message": "Indexación ya en progreso"}

        # Crear nueva tarea en background
        loop = asyncio.get_event_loop()
        self._indexing_task = loop.create_task(self.index_documents_async())

        return {"status": "started", "message": "Indexación iniciada en background"}

    def get_indexing_status(self):
        """Obtiene el estado actual de la indexación"""
        return {
            "is_indexing": self.is_indexing,
            "processed": self.processed_documents,
            "total": self.total_documents,
            "progress_percent": int((self.processed_documents / self.total_documents * 100)) if self.total_documents > 0 else 0,
            "error": self.indexing_error
        }

    def index_documents(self):
        """Método legacy - ahora solo wrapper síncrono (no recomendado)"""
        return self._index_documents_sync()

    async def reindex_all_documents(self):
        """Elimina y vuelve a indexar con control de flujo"""
        if self.is_indexing:
            return {"status": "error", "message": "Ya hay una indexación en progreso"}

        self.is_indexing = True
        try:
            print(f"Limpiando colección '{settings.COLLECTION_NAME}'...")
            from .database import engine as db_engine

            async with db_engine.begin() as conn:
                collection_uuid_result = await conn.execute(
                    text("SELECT uuid FROM langchain_pg_collection WHERE name = :name LIMIT 1"),
                    {"name": settings.COLLECTION_NAME}
                )
                collection_uuid = collection_uuid_result.scalar()

                if collection_uuid:
                    await conn.execute(
                        text("DELETE FROM langchain_pg_embedding WHERE collection_id = :uuid"),
                        {"uuid": collection_uuid}
                    )
                    print(f"✓ Eliminados todos los embeddings de la colección")
                else:
                    await conn.execute(text("DELETE FROM langchain_pg_embedding"))
                    print(f"✓ Tabla de embeddings limpiada")

            # Limpiar cache
            self._query_cache.clear()

            # Ejecutar indexación en background
            self.is_indexing = False  # Resetear para permitir nueva indexación
            return self.start_indexing_background()

        except Exception as e:
            print(f"Error en reindexación: {e}")
            self.is_indexing = False
            return {"status": "error", "message": str(e)}

    async def query(self, question: str):
        """Consulta al RAG optimizada con caché y búsqueda paralela"""

        # ✅ OPTIMIZACIÓN 2: Cache de consultas
        cache_key = question.lower().strip()
        current_time = time.time()

        if cache_key in self._query_cache:
            cached_result, timestamp = self._query_cache[cache_key]
            if current_time - timestamp < self._cache_ttl:
                print(f"✓ Respuesta desde caché (ahorro de ~3-5 segundos)")
                return cached_result

        # ✅ OPTIMIZACIÓN 3: Reducir k para búsquedas más rápidas
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )

        try:
            # ✅ OPTIMIZACIÓN 4: Timeout en la búsqueda
            context_docs = await asyncio.wait_for(
                asyncio.to_thread(retriever.invoke, question),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            return {
                "answer": "La búsqueda está tardando demasiado. Intenta con términos más específicos.",
                "sources": []
            }

        # ✅ OPTIMIZACIÓN 5: Agrupar por documento fuente para evitar redundancia
        docs_by_source = {}
        for doc in context_docs:
            source = doc.metadata.get('source', 'unknown')
            if source not in docs_by_source:
                docs_by_source[source] = []
            docs_by_source[source].append(doc.page_content)

        # Limitar contenido por fuente (máximo 500 chars por CV)
        context_text = "\n\n".join([
            f"FUENTE: {source}\n{' '.join(contents)[:500]}..."
            for source, contents in docs_by_source.items()
        ])

        # ✅ OPTIMIZACIÓN 6: Prompt más conciso
        prompt = ChatPromptTemplate.from_template(
            """Experto en Reclutamiento IT. Analiza CVs y selecciona los mejores.

            CONTEXTO:
            {context}

            FORMATO DE RESPUESTA (máximo 5 candidatos):
            ### [Nombre]
            [BOTON_CV:{{archivo.pdf}}]
            **Encaja porque:** [1-2 líneas]
            **Stack:** [Tecnologías clave]
            **Formación:** [Título principal]

            Pregunta: {question}"""
        )

        chain = prompt | self.llm

        try:
            # ✅ OPTIMIZACIÓN 7: Timeout para LLM
            response = await asyncio.wait_for(
                chain.ainvoke({"context": context_text, "question": question}),
                timeout=20.0
            )

            result = {
                "answer": response.content,
                "sources": list(docs_by_source.keys())
            }

            # Guardar en caché
            self._query_cache[cache_key] = (result, current_time)

            # Limpiar cache antiguo (mantener últimas 50 consultas)
            if len(self._query_cache) > 50:
                oldest_keys = sorted(
                    self._query_cache.keys(),
                    key=lambda k: self._query_cache[k][1]
                )[:10]
                for k in oldest_keys:
                    del self._query_cache[k]

            return result

        except asyncio.TimeoutError:
            return {
                "answer": "El modelo está tardando demasiado. Intenta reformular la pregunta.",
                "sources": []
            }
        except Exception as e:
            return {
                "answer": f"Error al procesar: {str(e)}",
                "sources": []
            }

    async def get_vector_count(self):
        """Contador de vectores optimizado"""
        try:
            from .database import engine as db_engine
            async with db_engine.connect() as conn:
                result = await conn.execute(
                    text("""
                        SELECT count(*)
                        FROM langchain_pg_embedding e
                        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                        WHERE c.name = :name
                    """),
                    {"name": settings.COLLECTION_NAME}
                )
                count = result.scalar()
                return count or 0
        except:
            return 0

    def clear_cache(self):
        """Método para limpiar la cache manualmente si es necesario"""
        self._query_cache.clear()
        print("Cache de consultas limpiada")

    def __del__(self):
        """Cleanup del engine síncrono"""
        if self._sync_engine is not None:
            self._sync_engine.dispose()
