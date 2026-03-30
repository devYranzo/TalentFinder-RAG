<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();

// Estados Reactivos
const query = ref('');
const respuesta = ref('');
const fuentes = ref([]);
const loading = ref(false);
const loadingIngest = ref(false);
const isReady = ref(false);

let statusInterval = null;
const totalFiles = ref(0);
const progreso = ref(0);
const processedDocuments = ref(0);
const totalDocuments = ref(0);

// Funciones
const calcularProgreso = (vectoresActuales, archivosTotales, processedDocs, totalDocs) => {
  if (totalDocs > 0 && processedDocs >= 0) {
    let porcentaje = Math.round((processedDocs / totalDocs) * 100);

    return Math.min(porcentaje, 95); // Máximo 95% mientras está indexando
  }
  
  // Fallback: usar vectores
  if (archivosTotales === 0) return 0;
  const metaEstimada = archivosTotales * 12; 
  let porcentaje = Math.round((vectoresActuales / metaEstimada) * 100);
  return Math.min(porcentaje, 95);
};

const checkStatus = async () => {
  const res = await axios.get('http://localhost:8000/status');
  const { total_vectors, total_files, is_indexing, processed_documents, total_documents } = res.data;

  totalFiles.value = total_files;
  processedDocuments.value = processed_documents || 0;
  totalDocuments.value = total_documents || 0;
  
  if (is_indexing) {
    progreso.value = calcularProgreso(total_vectors, total_files, processed_documents, total_documents);
  } else {
    // Si ya no está indexando
    if (loadingIngest.value) {
      progreso.value = 100;
      loadingIngest.value = false;
      isReady.value = total_vectors > 0;
      
      if (statusInterval) {
        clearInterval(statusInterval);
        statusInterval = null;
      }
    }
  }
};

const encenderMotor = async () => {
  loadingIngest.value = true;
  progreso.value = 0; // Resetear progreso
  try {
    await axios.post('http://localhost:8000/ingest');
    statusInterval = setInterval(checkStatus, 2000);
  } catch (error) {
    alert("Error al iniciar la ingesta");
    loadingIngest.value = false;
  }
};

const buscar = async () => {
  if (!query.value || !isReady.value) return;
  
  loading.value = true;
  respuesta.value = '';
  
  try {
    const res = await axios.get(`http://localhost:8000/search`, {
      params: { q: query.value }
    });
    respuesta.value = res.data.answer;
    fuentes.value = res.data.sources;
  } catch (error) {
    alert("Error en la conexión. Es posible que el servidor esté procesando demasiados datos.");
  } finally {
    loading.value = false;
  }
};

const obtenerRutaPdf = (fuente) => {
  if (!fuente) return '';
  
  // 1. Buscamos la palabra 'CVs/' en la ruta
  const marcador = 'CVs/';
  const indice = fuente.indexOf(marcador);
  
  if (indice !== -1) {
    // 2. Extraemos solo lo que hay DESPUÉS de 'CVs/'
    return fuente.substring(indice + marcador.length);
  }
  
  return fuente;
};

const renderizarMarkdown = (texto) => {
  return md.render(texto);
};

// Ciclo de vida
onMounted(() => {
  checkStatus();
  const generalInterval = setInterval(() => {
    if (!loadingIngest.value) {
      checkStatus();
    }
  }, 15000);
  
  const cleanup = () => {
    if (statusInterval) clearInterval(statusInterval);
    clearInterval(generalInterval);
  };

  window.$cleanup = cleanup;
});

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval);
});
</script>

<template>
  <div class="container mt-5">
    <header class="text-center mb-5">
      <h1 class="display-4"><i class="bi bi-cpu"></i>TalentFinder AI</h1>
      <p class="lead text-muted">Búsqueda semántica en base de datos de CVs</p>
      
      <div class="d-flex justify-content-center align-items-center gap-3 mt-4">
        <button 
          @click="encenderMotor" 
          :disabled="loadingIngest" 
          class="btn btn-sm shadow-sm"
          :class="isReady ? 'btn-success' : 'btn-outline-warning'"
        >
          <span v-if="loadingIngest" class="spinner-border spinner-border-sm me-2"></span>
          <i v-if="isReady" class="bi bi-check-circle-fill me-1"></i>
          {{ isReady ? 'Motor Listo' : 'Encender Motor' }}
        </button>
      </div>

      <div v-if="loadingIngest" class="mt-4 w-75 mx-auto">
        <div class="d-flex justify-content-between mb-1">
          <span class="text-muted small">
            <i class="bi bi-gear-fill spin"></i> Procesando 
            <strong>{{ processedDocuments }}/{{ totalDocuments }}</strong> documentos...
          </span>
          <span class="text-primary fw-bold">{{ progreso }}%</span>
        </div>
        
        <div class="progress" style="height: 10px;">
          <div 
            class="progress-bar progress-bar-striped progress-bar-animated" 
            role="progressbar" 
            :style="{ width: progreso + '%' }" 
            :aria-valuenow="progreso" 
            aria-valuemin="0" 
            aria-valuemax="100"
          ></div>
        </div>
      </div>
    </header>

    <div class="row justify-content-center mb-4">
      <div class="col-md-8">
        <div class="input-group input-group-lg shadow-sm" :style="{ opacity: isReady ? 1 : 0.5 }">
          <input 
            v-model="query" 
            @keyup.enter="isReady && buscar()"
            type="text" 
            class="form-control" 
            :placeholder="isReady ? 'Ej: Experto en Python...' : 'Active el motor primero...'"
            :disabled="!isReady || loading"
          >
          <button @click="buscar" class="btn btn-primary" :disabled="!isReady || loading || !query">
            <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
            <i v-else class="bi bi-search me-1"></i>
            Buscar
          </button>
        </div>
      </div>
    </div>

    <div v-if="respuesta" class="row justify-content-center">
      <div class="col-md-10">
        <div class="card shadow mb-4 border-0 border-start border-primary border-4">
          <div class="card-body">
            <h5 class="card-title text-primary"><i class="bi bi-robot"></i>Análisis de la IA</h5>
            <div class="card-text markdown-body" v-html="renderizarMarkdown(respuesta)"></div>
          </div>
        </div>

        <h5 class="mb-3"><i class="bi bi-journal-check"></i> Fuentes Relevantes (Haz clic para ver):</h5>
        <div class="list-group shadow-sm">
          <a 
            v-for="fuente in fuentes" 
            :key="fuente" 
            :href="'http://localhost:8000/pdfs/' + obtenerRutaPdf(fuente)" 
            target="_blank" 
            class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
          >
            <span><i class="bi bi-file-earmark-pdf text-danger me-2"></i> {{ fuente.split('/').pop() }}</span>
            <span class="badge bg-primary rounded-pill">Ver PDF <i class="bi bi-box-arrow-up-right ms-1"></i></span>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
body { 
  background-color: #f8f9fa; 
}

.card-text { 
  line-height: 1.6; color: #333; 
}

.input-group-lg .form-control { 
  border-radius: 0.5rem 0 0 0.5rem; 
}

.input-group-lg .btn { 
  border-radius: 0 0.5rem 0.5rem 0; 
}

.spin {
  animation: rotation 2s infinite linear;
  display: inline-block;
}

@keyframes rotation {
  from { transform: rotate(0deg); }
  to { transform: rotate(359deg); }
}

.progress {
  border-radius: 10px;
  background-color: #e9ecef;
}

.x-small {
  font-size: 0.75rem;
}

.markdown-body :deep(ul) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.5rem;
}

.markdown-body :deep(strong) {
  color: #0d6efd;
}

.markdown-body :deep(p) {
  margin-bottom: 1rem;
}
</style>