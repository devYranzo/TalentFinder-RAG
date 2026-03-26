from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
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

    def index_documents(self):
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
            return 0

        # 2. Splitter profesional
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = text_splitter.split_documents(new_docs)

        for chunk in chunks:
            # Reemplazamos el carácter nulo por un espacio vacío
            chunk.page_content = chunk.page_content.replace("\x00", "")

        # 3. Ingesta por lotes para no saturar memoria
        print(f"Indexando {len(new_docs)} archivos nuevos en lotes...")
        self.vector_store.add_documents(chunks, batch_size=100)

        return len(chunks)

    async def query(self, question: str):
        """Busca en vectores y responde con el LLM."""
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        # retriever.invoke suele ser síncrono en LangChain Community, se queda igual
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
        
        # 2. Añade 'await' aquí y usa 'ainvoke' (versión asíncrona)
        response = await chain.ainvoke({"context": context_text, "question": question})
        
        return {
            "answer": response.content,
            "sources": list(set([d.metadata.get("source") for d in context_docs]))
        }