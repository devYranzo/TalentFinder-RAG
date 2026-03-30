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
            temperature=0
        )
        self.is_indexing = False
        self.processed_documents = 0
        self.total_documents = 0

    def index_documents(self):
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

            # 1. Obtener qué archivos YA existentes en la DB para no duplicar
            existing_ids = set()
            try:
                # Buscamos en los metadatos de la colección
                data = self.vector_store.get()
                existing_ids = {doc['source'] for doc in data['metadatas']}
            except Exception:
                pass  # Si la tabla está vacía, seguimos

            new_docs = [d for d in docs if d.metadata.get('source') not in existing_ids]

            if not new_docs:
                print("No hay documentos nuevos para indexar.")
                self.processed_documents = 0
                return 0

            self.total_documents = len(new_docs)

            # 2. Splitter profesional
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            chunks = text_splitter.split_documents(new_docs)

            for chunk in chunks:
                # Reemplazamos el carácter nulo por un espacio vacío
                chunk.page_content = chunk.page_content.replace("\x00", "")

            # 3. Ingesta por lotes para no saturar memoria
            print(f"Indexando {len(new_docs)} archivos nuevos en lotes...")
            
            # Procesar por lotes y actualizar progreso
            lotes = [chunks[i:i+100] for i in range(0, len(chunks), 100)]
            for lote_idx, lote in enumerate(lotes):
                self.vector_store.add_documents(lote, batch_size=100)
                # Aproximar documentos procesados basado en chunks
                self.processed_documents = min(
                    int((lote_idx + 1) * len(lote) / len(chunks) * len(new_docs)),
                    len(new_docs)
                )
                print(f"Progreso: {self.processed_documents}/{len(new_docs)} documentos")

            return len(chunks)
        except Exception as e:
            print(f"Error durante indexación: {e}")
            return 0
        finally:
            self.is_indexing = False
            self.processed_documents = 0
            self.total_documents = 0

    async def query(self, question: str):
        """Busca en vectores y responde con el LLM."""
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        context_docs = retriever.invoke(question)
        
        context_text = "\n\n".join([
            f"FUENTE: {d.metadata.get('source')}\n{d.page_content}" 
            for d in context_docs
        ])

        prompt = ChatPromptTemplate.from_template(
            """Eres un asistente de RRHH estricto. 
            TU REGLA DE ORO: Responde ÚNICAMENTE basándote en el contexto proporcionado abajo.
            
            CONTEXTO DE LOS CVs:
            {context}
            
            INSTRUCCIONES:
            1. Si la información no está en el contexto, di exactamente: "Lo siento, no encuentro información sobre eso en los CVs cargados".
            2. No uses tu conocimiento general.
            3. Si mencionas a alguien, indica de qué archivo viene la información.
            
            Pregunta del reclutador: {question}"""
        )
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({"context": context_text, "question": question})
        
        return {
            "answer": response.content,
            "sources": list(set([d.metadata.get("source") for d in context_docs]))
        }

    async def get_vector_count(self):
        """Calcula cuántos registros hay en la tabla de embeddings."""
        try:
            from .database import engine as db_engine 
            
            async with db_engine.connect() as conn:
                result = await conn.execute(text("SELECT count(*) FROM langchain_pg_embedding"))
                count = result.scalar()
                return count or 0
        except Exception as e:
            print(f"Error al contar vectores: {e}")
            return 0