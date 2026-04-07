<script setup>
defineProps({
  isReady: {
    type: Boolean,
    default: false,
  },
  loadingIngest: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['encender', 'reindexar']);
</script>

<template>
  <header class="text-center mb-4">
    <div class="d-flex align-items-center justify-content-between mb-3">
      <h1 class="display-5 fw-bold text-primary mb-0">
        <i class="bi bi-people me-2 text-dark"></i>Talent <span class="text-dark">Finder</span>
      </h1>
      <div class="d-flex gap-2">
        <!-- Botón de indexar (solo documentos nuevos) -->
        <button
          v-if="!isReady && !loadingIngest"
          @click="emit('encender')"
          class="btn btn-success btn-sm rounded-pill shadow p-2"
          :disabled="loadingIngest"
        >
          <i class="bi bi-power me-1"></i>Indexar CVs
        </button>

        <!-- Botón de reindexar (todos los documentos) -->
        <button
          v-if="isReady && !loadingIngest"
          @click="emit('reindexar')"
          class="btn btn-warning btn-sm rounded-pill shadow p-2"
          :disabled="loadingIngest"
          title="Elimina todos los vectores y vuelve a indexar desde cero"
        >
          <i class="bi bi-arrow-clockwise me-1"></i>Reindexar CVs
        </button>
      </div>
    </div>

    <div class="row justify-content-center">
      <div v-if="isReady" class="col-4 alert alert-success py-2 rounded-pill">
        <i class="bi bi-check-circle-fill me-2"></i>
        <strong>Sistema listo</strong> - Puedes realizar búsquedas
      </div>
      <div v-else-if="!loadingIngest" class="col-4 alert alert-warning py-2 rounded-pill">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <strong>Sistema sin indexar</strong> - Haz clic en "Indexar CVs" para comenzar
      </div>
    </div>
  </header>
</template>

<style scoped>
.alert {
  font-size: 0.9rem;
}
</style>
