import time
import asyncio
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import text

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

    def index_documents(self):
        """Indexa solo documentos nuevos evitando saturación de API"""
        self.is_indexing = True
        self.processed_documents = 0

        try:
            loader = DirectoryLoader(
                settings.PDF_PATH,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                recursive=True
            )
            docs = loader.load()

            # 1. Obtener archivos existentes de forma más eficiente
            existing_ids = set()
            try:
                # Limitamos la búsqueda para no saturar la memoria local
                results = self.vector_store.similarity_search("", k=5000)
                existing_ids = {doc.metadata.get('source') for doc in results if doc.metadata.get('source')}
            except Exception as e:
                print(f"Aviso: No se pudieron obtener documentos existentes (posible tabla vacía): {e}")

            new_docs = [d for d in docs if d.metadata.get('source') not in existing_ids]

            if not new_docs:
                print("No hay documentos nuevos para indexar.")
                return 0

            self.total_documents = len(new_docs)

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = text_splitter.split_documents(new_docs)

            for chunk in chunks:
                chunk.page_content = chunk.page_content.replace("\x00", "")

            # 2. Ingesta por lotes con PAUSA (Crucial para evitar Error 429)
            print(f"Indexando {len(new_docs)} archivos nuevos...")

            # Lotes más pequeños para la capa gratuita (Free Tier)
            batch_size = 25
            lotes = [chunks[i:i+batch_size] for i in range(0, len(chunks), batch_size)]

            for lote_idx, lote in enumerate(lotes):
                self.vector_store.add_documents(lote)

                # Actualizar progreso
                self.processed_documents = min(
                    int((lote_idx + 1) * len(lote) / len(chunks) * len(new_docs)),
                    len(new_docs)
                )
                print(f"Progreso: {self.processed_documents}/{len(new_docs)} documentos")

                # CORRECCIÓN: Pausa de 2 segundos entre lotes para no saturar los Embeddings de Google
                time.sleep(2)

            return len(chunks)
        except Exception as e:
            print(f"Error crítico durante indexación: {e}")
            return 0
        finally:
            self.is_indexing = False

    async def reindex_all_documents(self):
        """Elimina y vuelve a indexar con control de flujo"""
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
                else:
                    await conn.execute(text("DELETE FROM langchain_pg_embedding"))

            # Reutilizar la lógica de indexación estándar
            return self.index_documents()
        except Exception as e:
            print(f"Error en reindexación: {e}")
            return 0
        finally:
            self.is_indexing = False

    async def query(self, question: str):
        """Consulta al RAG con manejo de contexto"""
        # Aumentamos ligeramente k para tener más variedad, pero sin exagerar
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 7})
        context_docs = retriever.invoke(question)

        context_text = "\n\n".join([
            f"FUENTE: {d.metadata.get('source')}\n{d.page_content}"
            for d in context_docs
        ])

        prompt = ChatPromptTemplate.from_template(
            """Eres un experto en Reclutamiento IT. Analiza los CVs y selecciona a los mejores.

            CONTEXTO DE LOS CVs:
            {context}

            REGLAS DE RESPUESTA:
            1. Usa una lista numerada del 1 al 5.
            2. Formato EXACTO:
            ### [Nombre del Candidato]
            [BOTON_CV:{{nombre_archivo_pdf}}]
            **Por qué encaja:** [Resumen breve]
            **Experiencia Clave:** [Tecnologías relevantes]
            **Estudios:** [Formación encontrada]
            **Certificaciones/Otros estudios:** [Certificaciones]

            3. Sustituye {{nombre_archivo_pdf}} por la ruta exacta de la FUENTE.
            4. Si no hay candidatos, indica que no se encontraron perfiles.

            Pregunta del reclutador: {question}"""
        )

        chain = prompt | self.llm

        try:
            response = await chain.ainvoke({"context": context_text, "question": question})
            return {
                "answer": response.content,
                "sources": list(set([d.metadata.get("source") for d in context_docs]))
            }
        except Exception as e:
            return {
                "answer": f"Error al procesar la consulta: El modelo está saturado o hubo un problema de conexión. Detalle: {str(e)}",
                "sources": []
            }

    async def get_vector_count(self):
        """Contador de vectores en base de datos"""
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
