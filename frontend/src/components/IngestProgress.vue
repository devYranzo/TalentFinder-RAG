<script setup>
defineProps({
  progreso: {
    type: Number,
    default: 0,
  },
});
</script>

<template>
  <transition name="fade">
    <div class="mt-5 p-4 border rounded-4 bg-white shadow-sm mx-auto mb-2" style="max-width: 600px">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <span class="small text-secondary fw-bold">
          <i class="bi bi-arrow-repeat spin me-2"></i>Procesando documentos...
        </span>
        <span class="badge bg-primary rounded-pill">{{ progreso }}%</span>
      </div>
      <div class="progress" style="height: 12px; border-radius: 6px">
        <div
          class="progress-bar progress-bar-striped progress-bar-animated bg-primary"
          :style="{ width: progreso + '%' }"
        ></div>
      </div>
      <p class="x-small text-muted mt-2 mb-0">
        Esto puede tardar unos minutos dependiendo del volumen de archivos.
      </p>
    </div>
  </transition>
</template>

<style scoped>
.spin {
  animation: rotation 1.5s infinite linear;
  display: inline-block;
}

@keyframes rotation {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(359deg);
  }
}

.x-small {
  font-size: 0.75rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
