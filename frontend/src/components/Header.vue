<script setup>
import { useRoute } from 'vue-router';

defineProps({
  isReady: {
    type: Boolean,
    default: false,
  },
  loadingIngest: {
    type: Boolean,
    default: false,
  },
  isDark: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['encender', 'reindexar', 'toggle-theme']);
const route = useRoute();
</script>

<template>
  <header class="my-3">
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
      <h1 class="display-6 fw-bold text-primary mb-0 pe-3 border-end">
        <i class="bi bi-people me-2 text-dark"></i>Talent <span class="text-dark">Finder</span>
      </h1>

      <div class="nav nav-pills bg-light rounded-pill shadow-sm">
        <router-link
          to="/"
          class="nav-link rounded-pill px-4"
          :class="{ active: route.path === '/' }"
        >
          <i class="bi bi-search me-1"></i> Buscador
        </router-link>
        <router-link
          to="/filemanager"
          class="nav-link rounded-pill px-4"
          :class="{ active: route.path === '/filemanager' }"
        >
          <i class="bi bi-folder-fill me-1"></i> Gestión CVs
        </router-link>
      </div>

      <div class="d-flex gap-2 align-items-center">
        <button
          v-if="!isReady && !loadingIngest"
          @click="emit('encender')"
          class="btn btn-success rounded-pill shadow-sm px-3"
          :disabled="loadingIngest"
        >
          <i class="bi bi-lightning-charge-fill me-1"></i>Indexar
        </button>

        <button
          v-if="isReady && !loadingIngest"
          @click="emit('reindexar')"
          class="btn btn-warning rounded-pill shadow-sm px-3"
          :disabled="loadingIngest"
          title="Reindexar todo desde cero"
        >
          <i class="bi bi-arrow-clockwise me-1"></i>Reindexar
        </button>

        <button
          @click="emit('toggle-theme')"
          class="btn btn-outline-secondary rounded-pill shadow-sm"
          :title="isDark ? 'Modo claro' : 'Modo oscuro'"
        >
          <i :class="isDark ? 'bi bi-sun-fill' : 'bi bi-moon-fill'"></i>
        </button>
      </div>
    </div>

    <div class="row justify-content-center mx-0">
      <div
        v-if="isReady"
        class="col-md-6 alert alert-success py-2 rounded-pill shadow-sm border-0 text-center"
      >
        <i class="bi bi-check-circle-fill me-2"></i>
        Motor RAG <strong>Activo</strong> - Base de datos sincronizada
      </div>
      <div
        v-else-if="!loadingIngest"
        class="col-md-8 alert alert-warning py-3 rounded-4 shadow-sm border-0"
      >
        <div class="d-flex align-items-center justify-content-center text-center text-md-start">
          <i class="bi bi-database-fill-exclamation fs-3 me-3 d-none d-md-block"></i>
          <div>
            <div class="fw-bold">Acción requerida: El sistema no tiene datos</div>
            <div class="small">
              Sube archivos en <strong>Gestión CVs</strong> y luego pulsa el botón
              <strong>Indexar</strong>.
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.nav-pills .nav-link {
  color: #6c757d;
  font-weight: 500;
  transition: all 0.3s ease;
}
.nav-pills .nav-link.active {
  background-color: #0d6efd;
  color: white;
  box-shadow: 0 4px 10px rgba(13, 110, 253, 0.2);
}
.alert {
  font-size: 0.95rem;
}
</style>
