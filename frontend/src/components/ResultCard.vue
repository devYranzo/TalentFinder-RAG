<script setup>
import MarkdownIt from 'markdown-it';
import api from '@/services/api';

const md = new MarkdownIt({ html: true, linkify: true });

defineProps({
  respuesta: String,
  copiado: Boolean,
});

defineEmits(['copiar']);

window.abrirArchivoCV = (ruta) => {
  const url = api.getPdfUrl(ruta);
  window.open(url, '_blank');
};

const renderizarRespuesta = (texto) => {
  if (!texto) return '';
  let html = md.render(texto);
  const regex = /\[BOTON_CV:(.*?)\]/g;
  return html.replace(
    regex,
    (match, ruta) => `
      <div class="mt-2 mb-4">
        <button onclick="window.abrirArchivoCV('${ruta.trim()}')"
          class="btn btn-sm btn-outline-primary shadow-sm rounded-pill px-3">
          <i class="bi bi-file-earmark-pdf-fill me-1"></i> Abrir Curriculum Vitae
        </button>
      </div>
    `
  );
};
</script>

<template>
  <transition name="slide">
    <div v-if="respuesta" class="row justify-content-center">
      <div class="col-lg-10">
        <div class="card shadow-lg border-0 rounded-4 overflow-hidden result-card mb-5">
          <div
            class="card-header bg-primary text-white py-3 px-4 d-flex align-items-center justify-content-between"
          >
            <div class="d-flex align-items-center">
              <i class="bi bi-stars fs-4 me-2"></i>
              <h5 class="mb-0 fw-bold">Análisis del top 5 <b>Mejores Candidatos</b></h5>
            </div>

            <button
              @click="$emit('copiar')"
              class="btn btn-sm btn-light rounded-pill px-3 fw-bold shadow-sm d-flex align-items-center"
              :class="{ 'btn-success text-white': copiado }"
            >
              <i :class="['bi me-2', copiado ? 'bi-check-lg' : 'bi-clipboard-plus']"></i>
              {{ copiado ? '¡Copiado!' : 'Copiar' }}
            </button>
          </div>

          <div class="card-body p-4 p-md-5">
            <div class="markdown-body" v-html="renderizarRespuesta(respuesta)"></div>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.markdown-body:deep(h3) {
  font-size: 1.4rem;
  color: #0d6efd;
  border-bottom: 2px solid #f0f4f8;
  padding-bottom: 0.5rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.markdown-body:deep(h3::before) {
  content: 'Candidato';
  font-size: 0.7rem;
  text-transform: uppercase;
  background: #0d6efd;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 10px;
}

.markdown-body:deep(strong) {
  color: #2c3e50;
  font-weight: 700;
}

.markdown-body:deep(ul) {
  padding-left: 1.2rem;
  margin-bottom: 1.5rem;
}

.markdown-body:deep(li) {
  margin-bottom: 0.4rem;
  position: relative;
}

.btn-light {
  background-color: rgba(255, 255, 255, 0.9);
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-light:hover {
  background-color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.btn-success {
  background-color: #28a745 !important;
  border-color: #28a745 !important;
  animation: pulse 0.4s ease-in-out;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

.slide-enter-active {
  transition: all 0.5s ease-out;
}
.slide-enter-from {
  transform: translateY(30px);
  opacity: 0;
}
</style>
