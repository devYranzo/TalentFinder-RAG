# TalentFinder RAG: Análisis Inteligente de CVs

**TalentFinder** es una solución avanzada de reclutamiento basada en **RAG (Retrieval-Augmented Generation)**. Permite a los departamentos de RRHH indexar cientos de currículos en PDF y realizar consultas complejas en lenguaje natural para identificar a los candidatos ideales basándose en su experiencia, formación y certificaciones.

---

## 🛠️ Stack Tecnológico

- **Frontend:** Vue.js 3 (Composition API), Vite, Bootstrap 5.
- **Backend:** FastAPI (Python 3.10+), LangChain.
- **Base de Datos Vectorial:** PostgreSQL + **PGVector**.
- **LLM:** Gemini-2.5-flash / intfloat/multilingual-e5-small.
- **Infraestructura:** Docker & Docker Compose.

---

## ✨ Características Destacadas

- **🔍 Búsqueda Semántica:** Entiende conceptos técnicos y contextos, no solo palabras clave.
- **📊 Monitorización en Tiempo Real:** Barra de progreso reactiva en el frontend que muestra el estado de la indexación.
- **📋 Copiado Profesional:** Botón para copiar resultados con limpieza automática de Markdown para informes de RRHH.
- **🐳 Dockerizado:** Despliegue sencillo con un solo comando, configurado para entornos de red local (CORS habilitado).

---

## 🚀 Instalación y Despliegue

### Requisitos Previos

- Docker y Docker Compose instalado.
- API Key de Gemini AI.

### Pasos para arrancar

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/talentfinder-rag.git](https://github.com/tu-usuario/talentfinder-rag.git)
   cd talentfinder-rag
   ```

---

## 🏗️ Arquitectura del Sistema

El flujo de trabajo sigue el estándar RAG para garantizar respuestas precisas basadas únicamente en los documentos proporcionados:

1.  **Ingesta:** Los archivos PDF se cargan y se limpian de caracteres nulos (`\x00`) para compatibilidad con PostgreSQL.
2.  **Fragmentación (Splitting):** Se utiliza `RecursiveCharacterTextSplitter` (1000 chars, 150 overlap) para mantener el contexto de estudios y experiencia en cada fragmento.
3.  **Embeddings & Storage:** Generación de vectores y almacenamiento en **PGVector** con filtrado de duplicados por metadatos de origen.
4.  **Recuperación:** Al realizar una búsqueda, el sistema recupera los fragmentos más relevantes y el LLM genera un ranking detallado de los 5 mejores candidatos.

---

## 🚀 Instalación y Despliegue

### Requisitos Previos

- Docker y Docker Compose instalados.
- API Key de OpenAI válida.

### Pasos para arrancar

1.  **Clonar el repositorio:**

    ```bash
    git clone [https://github.com/tu-usuario/talentfinder-rag.git](https://github.com/tu-usuario/talentfinder-rag.git)
    cd talentfinder-rag
    ```

2.  **Configurar el entorno:**
    Crea un archivo `.env` en la raíz del proyecto:

    ```env
    GOOGLE_API_KEY=tu_api_key_aquí
    DATABASE_URL=postgresql+psycopg://user:password@db:5432/rag_db
    ```

3.  **Desplegar con Docker:**

    ```bash
    docker compose build --no-cache
    ```

    ```bash
    docker compose up -d
    ```

4.  **Acceso:**
    - **Frontend:** `http://localhost`
    - **API (Docs Swagger):** `http://localhost:8000/docs`

---

## 📂 Estructura del Proyecto

```text
├── backend/
│   ├── app/
│   │   ├── engine.py       # Motor RAG, Splitter y lógica de vectores
│   │   ├── main.py         # Endpoints FastAPI y Scheduler de tareas
│   │   ├── config.py       # Gestión de variables de entorno
|   |   └── database.py     # Embedding, vector store
│   └── CVs/                # Almacenamiento persistente de currículums
├── frontend/
│   ├── src/
│   │   ├── components/     # UI Componentes (Header, Resultados, etc.)
│   │   ├── composables/    # Lógica de estado reactivo (useMotorStatus)
│   │   └── services/       # Cliente Axios y API Service
│   └── App.vue             # Componente raíz
└── docker-compose.yml      # Orquestación de Frontend, Backend y DB
```

---

## 🤝 Autor

Proyecto desarrollado por devYranzo - 2026.
