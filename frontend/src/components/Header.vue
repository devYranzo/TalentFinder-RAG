<script setup>
defineProps({
  isReady: Boolean,
  loadingIngest: Boolean,
});

defineEmits(['encender']);
</script>

<template>
  <header class="text-center mb-5">
    <h1 class="fw-bold">TalentFinder <span class="text-primary text-gradient">AI</span></h1>
    <p class="text-muted lead">Buscador inteligente de perfiles y análisis de CVs</p>

    <div class="mt-4">
      <button
        @click="$emit('encender')"
        :disabled="isReady || loadingIngest"
        :class="[
          'btn px-5 py-2 fw-bold shadow-sm border-0 transition-all',
          isReady ? 'btn-success' : 'btn-warning text-dark',
        ]"
      >
        <i :class="['bi me-2', isReady ? 'bi-check-circle-fill' : 'bi-lightning-charge-fill']"></i>
        {{ isReady ? 'Motor Listo para Buscar' : 'Encender Motor de Análisis' }}
      </button>
    </div>
  </header>
</template>

<style scoped>
.transition-all {
  transition: all 0.3s ease;
}

.text-gradient {
  background: linear-gradient(90deg, #0d6efd, #6610f2);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
