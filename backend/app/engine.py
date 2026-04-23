import time
import asyncio
import re
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
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
            max_retries=3,
            timeout=120,
            request_timeout=120
        )
        self.is_indexing = False
        self.processed_documents = 0
        self.total_documents = 0
        self.indexing_error: Optional[str] = None
        self._query_cache = {}
        self._cache_ttl = 300
        self._sync_engine = None
        self._indexing_task: Optional[asyncio.Task] = None

    def _get_sync_engine(self):
        if self._sync_engine is None:
            db_url = settings.DATABASE_URL.replace('+asyncpg', '')
            self._sync_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600
            )
        return self._sync_engine

    def _index_documents_sync(self):
        """Lógica de indexación optimizada de rag_background"""
        self.indexing_error = None
        try:
            loader = DirectoryLoader(
                settings.PDF_PATH,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                recursive=True
            )
            docs = loader.load()

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
            except Exception as e:
                print(f"Aviso: Error en documentos existentes: {e}")

            new_docs = [d for d in docs if d.metadata.get('source') not in existing_ids]
            if not new_docs: return 0

            self.total_documents = len(new_docs)
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = text_splitter.split_documents(new_docs)

            for chunk in chunks:
                chunk.page_content = chunk.page_content.replace("\x00", "")

            batch_size = 20
            lotes = [chunks[i:i+batch_size] for i in range(0, len(chunks), batch_size)]

            for lote_idx, lote in enumerate(lotes):
                if not self.is_indexing: break
                try:
                    self.vector_store.add_documents(lote)
                    self.processed_documents = min(
                        int((lote_idx + 1) * len(lote) / len(chunks) * len(new_docs)),
                        len(new_docs)
                    )
                    time.sleep(1.5 if lote_idx < 10 else 2.5)
                except Exception as e:
                    time.sleep(5)
                    continue

            self._query_cache.clear()
            return len(chunks)
        except Exception as e:
            self.indexing_error = str(e)
            return 0

    async def index_documents_async(self):
        if self.is_indexing: return {"status": "already_running"}
        self.is_indexing = True
        try:
            result = await asyncio.to_thread(self._index_documents_sync)
            return {"status": "completed", "chunks": result}
        finally:
            self.is_indexing = False

    def start_indexing_background(self):
        if self._indexing_task and not self._indexing_task.done():
            return {"status": "already_running"}
        loop = asyncio.get_event_loop()
        self._indexing_task = loop.create_task(self.index_documents_async())
        return {"status": "started"}

    async def query(self, question: str):
        """Consulta fusionada: Filtro de duplicados + Post-procesamiento"""
        start_time = time.time()
        cache_key = question.lower().strip()
        current_time = time.time()

        if cache_key in self._query_cache:
            res, ts = self._query_cache[cache_key]
            if current_time - ts < self._cache_ttl:
                return res

        retriever = self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 10, "fetch_k": 25, "lambda_mult": 0.7}
        )

        try:
            context_docs = await asyncio.wait_for(
                asyncio.to_thread(retriever.invoke, question), timeout=6.0
            )
        except asyncio.TimeoutError:
            return {"answer": "Timeout en búsqueda.", "sources": []}

        docs_by_source = {}
        for doc in context_docs:
            source = doc.metadata.get('source', 'unknown')
            if source not in docs_by_source:
                docs_by_source[source] = []
            if len(docs_by_source[source]) < 2:
                docs_by_source[source].append(doc.page_content)

        context_parts = []
        base_path = settings.PDF_PATH.rstrip('/')

        for source, contents in docs_by_source.items():
            full_text_raw = ' '.join(contents)
            clean_text = full_text_raw.replace('\x00', '')[:1000]

            rel_path = source.replace(base_path, "").lstrip('/')

            context_parts.append(f"ARCHIVO ORIGEN: {rel_path}\nCONTENIDO:\n{clean_text}")

        context_text = "\n\n---\n\n".join(context_parts)

        prompt = ChatPromptTemplate.from_template(
            """
            Eres un motor de selección de personal estricto. Tu salida debe contener ÚNICAMENTE los 5 mejores candidatos.

            INSTRUCCIONES DE SALIDA:
            1. Prohibido listar candidatos que no estén en el Top 5.
            2. No escribas introducciones, ni análisis previos, ni conclusiones finales.
            3. Si encuentras más de 5 candidatos interesantes, descarta los menos relevantes y quédate SOLO con los 5 mejores.

            FORMATO POR CANDIDATO (Repetir exactamente 5 veces):
            ### [Nombre y Apellidos]
            [BOTON_CV:{{filename}}]
            **Por qué encaja:** [Explicación detallada de su ranking] <br />
            **Experiencia:** [Tecnologías clave] <br />
            **Estudios:** [Estudios reglados] <br />

            ---
            DATOS DE LOS CVS:
            {context}

            SOLICITUD: {question}

            IMPORTANTE: En {{filename}} pon la ruta exacta que aparece en "ARCHIVO ORIGEN".
            """
        )

        chain = prompt | self.llm

        try:
            response = await chain.ainvoke({"context": context_text, "question": question})
            answer = str(response.content)

            answer = answer.replace('[Nombre Candidato]', '').replace('[Nombre]', '')

            seen_files = set()
            cleaned_lines = []
            skip_section = False

            for line in answer.split('\n'):
                cv_match = re.search(r'\[BOTON_CV:([^\]]+)\]', line)
                if cv_match:
                    fname = cv_match.group(1)
                    if fname in seen_files:
                        skip_section = True
                        continue
                    seen_files.add(fname)
                    skip_section = False

                if line.strip().startswith('###'): skip_section = False
                if not skip_section: cleaned_lines.append(line)

            final_answer = '\n'.join(cleaned_lines)
            result = {"answer": final_answer, "sources": list(docs_by_source.keys())}
            self._query_cache[cache_key] = (result, current_time)
            return result

        except Exception as e:
            return {"answer": f"Error: {str(e)}", "sources": []}

    # --- Métodos de utilidad de engine.py ---
    async def get_vector_count(self):
        try:
            from .database import engine as db_engine
            async with db_engine.connect() as conn:
                res = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding"))
                return res.scalar() or 0
        except: return 0

    async def get_indexed_documents_count(self):
        try:
            from .database import engine as db_engine
            async with db_engine.connect() as conn:
                res = await conn.execute(text("SELECT count(DISTINCT cmetadata->>'source') FROM langchain_pg_embedding"))
                return res.scalar() or 0
        except: return 0

    async def get_indexing_status_complete(self):
        v_count = await self.get_vector_count()
        d_count = await self.get_indexed_documents_count()
        return {
            **self.get_indexing_status(),
            "has_data": v_count > 0,
            "vectors_count": v_count,
            "documents_count": d_count
        }

    def get_indexing_status(self):
        return {
            "is_indexing": self.is_indexing,
            "processed": self.processed_documents,
            "total": self.total_documents,
            "progress_percent": int((self.processed_documents/self.total_documents*100)) if self.total_documents > 0 else 0,
            "error": self.indexing_error
        }

    async def reindex_all_documents(self):
        """Elimina todo y vuelve a indexar"""
        try:
            sync_engine = self._get_sync_engine()
            with sync_engine.connect() as conn:
                conn.execute(text("DELETE FROM langchain_pg_embedding"))
                conn.commit()
            return self.start_indexing_background()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def is_indexed(self) -> bool:
        return await self.get_vector_count() > 0

    def clear_cache(self):
        self._query_cache.clear()
        return {"status": "cache_cleared"}
