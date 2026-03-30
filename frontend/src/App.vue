<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';

// --- CONFIGURACIÓN ---
const md = new MarkdownIt({ html: true, linkify: true });

// --- ESTADOS REACTIVOS ---
const query = ref('');
const respuesta = ref('');
const loading = ref(false);
const loadingIngest = ref(false);
const progreso = ref(0);
const motorStatus = ref({
  is_ready: false,
  total_vectors: 0,
  total_files: 0,
  is_indexing: false
});

let statusInterval = null;

// --- PROPIEDADES COMPUTADAS ---
const isReady = computed(() => motorStatus.value.is_ready || motorStatus.value.total_vectors > 0);
const canSearch = computed(() => isReady.value && !loading.value && query.value.trim().length > 0);

// --- LÓGICA DE ESTADO (POLLING INTELIGENTE) ---
const checkStatus = async () => {
  try {
    const { data } = await axios.get('http://localhost:8000/status');
    motorStatus.value = data;

    if (data.is_indexing) {
      loadingIngest.value = true;
      
      if (data.total_documents > 0) {
        const porcentajeReal = Math.round((data.processed_documents / data.total_documents) * 100);
        
        progreso.value = Math.min(porcentajeReal, 99); 
      }
    } else {
      if (loadingIngest.value) {
        progreso.value = 100;
        setTimeout(() => { 
          loadingIngest.value = false;
          motorStatus.value.is_ready = true;
        }, 1500);
      }
      detenerIntervalo();
    }
  } catch (e) {
    console.error("Error en polling:", e);
  }
};

const iniciarIntervalo = () => {
  if (!statusInterval) {
    statusInterval = setInterval(checkStatus, 2500);
  }
};

const detenerIntervalo = () => {
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }
};

const encenderMotor = async () => {
  if (loadingIngest.value) return;
  loadingIngest.value = true;
  progreso.value = 0;
  try {
    await axios.post('http://localhost:8000/ingest');
    iniciarIntervalo();
  } catch (error) {
    loadingIngest.value = false;
    alert("No se pudo iniciar el proceso de ingesta.");
  }
};

const buscar = async () => {
  if (!canSearch.value) return;
  loading.value = true;
  respuesta.value = '';
  try {
    const res = await axios.get(`http://localhost:8000/search`, {
      params: { q: query.value }
    });
    respuesta.value = res.data.answer;
  } catch (error) {
    alert("Error en la búsqueda. El servidor podría estar saturado.");
  } finally {
    loading.value = false;
  }
};

// --- GESTIÓN DE PDF Y RENDERIZADO ---
window.abrirArchivoCV = (ruta) => {
  // Limpiamos la ruta por si la IA añade "CVs/" al principio
  const rutaLimpia = ruta.replace(/^CVs\//, '');
  const url = `http://localhost:8000/pdfs/${rutaLimpia}`;
  window.open(url, '_blank');
};

const renderizarRespuesta = (texto) => {
  if (!texto) return '';
  let html = md.render(texto);
  
  // Reemplaza el tag [BOTON_CV:ruta] por un botón real
  const regex = /\[BOTON_CV:(.*?)\]/g;
  return html.replace(regex, (match, ruta) => `
    <div class="mt-2 mb-4">
      <button onclick="window.abrirArchivoCV('${ruta.trim()}')" class="btn btn-sm btn-outline-primary shadow-sm rounded-pill px-3">
        <i class="bi bi-file-earmark-pdf-fill me-1"></i> Abrir Curriculum Vitae
      </button>
    </div>
  `);
};

// --- CICLO DE VIDA ---
onMounted(async () => {
  await checkStatus();
  if (motorStatus.value.is_indexing) {
    iniciarIntervalo();
  }
});

onUnmounted(() => {
  detenerIntervalo();
});
</script>

<template>
  <div class="container pt-5">
    <header class="text-center mb-5">
      <h1 class="fw-bold">TalentFinder <span class="text-primary text-gradient">AI</span></h1>
      <p class="text-muted lead">Buscador inteligente de perfiles y análisis de CVs</p>

      <div class="mt-4">
        <button 
          @click="encenderMotor" 
          :disabled="isReady || loadingIngest"
          :class="['btn px-5 py-2 fw-bold shadow-sm border-0 transition-all', isReady ? 'btn-success' : 'btn-warning text-dark']"
        >
          <i :class="['bi me-2', isReady ? 'bi-check-circle-fill' : 'bi-lightning-charge-fill']"></i>
          {{ isReady ? 'Motor Listo para Buscar' : 'Encender Motor de Análisis' }}
        </button>
      </div>

      <transition name="fade">
        <div v-if="loadingIngest" class="mt-5 p-4 border rounded-4 bg-white shadow-sm mx-auto" style="max-width: 600px;">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="small text-secondary fw-bold">
              <i class="bi bi-arrow-repeat spin me-2"></i>Procesando documentos...
            </span>
            <span class="badge bg-primary rounded-pill">{{ progreso }}%</span>
          </div>
          <div class="progress" style="height: 12px; border-radius: 6px;">
            <div 
              class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
              :style="{ width: progreso + '%' }"
            ></div>
          </div>
          <p class="x-small text-muted mt-2 mb-0">Esto puede tardar unos minutos dependiendo del volumen de archivos.</p>
        </div>
      </transition>
    </header>

    <transition name="slide">
      <div v-if="respuesta" class="row justify-content-center">
        <div class="col-lg-10">
          <div class="card shadow border-0 rounded-4 overflow-hidden result-card mb-5">
            <div class="card-header bg-primary text-white py-3 px-4 d-flex align-items-center">
              <i class="bi bi-stars fs-4 me-2"></i>
              <h5 class="mb-0 fw-bold">Análisis de los Mejores Candidatos</h5>
            </div>
            <div class="card-body p-4 p-md-5">
              <div class="markdown-body" v-html="renderizarRespuesta(respuesta)"></div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <div class="sticky-search-container">
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div class="search-container shadow-lg rounded-pill p-1 bg-white border border-light">
            <div class="input-group input-group-lg">
              <span class="input-group-text bg-transparent border-0 ps-4">
                <i class="bi bi-search text-primary opacity-50"></i>
              </span>
              <input 
                v-model="query" 
                @keyup.enter="buscar"
                type="text" 
                class="form-control border-0 rounded-pill shadow-none ps-2"
                :placeholder="isReady ? 'Ej: Ingeniero de redes con certificación CCNP...' : 'Active el motor para buscar...'"
                :disabled="!isReady || loading"
              >
              <button @click="buscar" class="btn btn-primary rounded-pill px-4 mx-1 fw-bold my-1 shadow" :disabled="!canSearch">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? 'Analizando...' : 'Buscar' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container { 
  max-width: 1100px;
}

.transition-all { 
  transition: all 0.3s ease; 
}

.spin {
  animation: rotation 1.5s infinite linear;
  display: inline-block;
}

@keyframes rotation { 
  from { transform: rotate(0deg); } 
  to { transform: rotate(359deg); } 
}

.sticky-search-container {
  position: sticky;
  bottom: 1rem;  
  z-index: 20;
  transition: all 0.3s ease;
}

.search-container {
  display: flex;
  transition: transform 0.2s;
}

.search-container:focus-within {
  transform: scale(1.02);
}

.markdown-body :deep(h3) {
  font-size: 1.4rem;
  color: #0d6efd;
  border-bottom: 2px solid #f0f4f8;
  padding-bottom: 0.5rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.markdown-body :deep(h3::before) {
  content: "Candidato";
  font-size: 0.7rem;
  text-transform: uppercase;
  background: #0d6efd;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 10px;
}

.markdown-body :deep(strong) {
  color: #2c3e50;
  font-weight: 700;
}

.markdown-body :deep(ul) {
  padding-left: 1.2rem;
  margin-bottom: 1.5rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.4rem;
  position: relative;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.4s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-enter-active { transition: all 0.5s ease-out; }
.slide-enter-from { transform: translateY(30px); opacity: 0; }

.x-small { font-size: 0.75rem; }
.text-gradient {
  background: linear-gradient(90deg, #0d6efd, #6610f2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>