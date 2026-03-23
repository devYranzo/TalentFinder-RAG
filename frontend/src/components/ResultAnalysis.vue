<script setup>
const props = defineProps({
  content: {
    type: String,
    required: true,
    default: 'No se generó ningún análisis.'
  }
});
</script>

<template>
  <div class="card border-0 shadow-lg mb-4 overflow-hidden">
    <div class="card-header bg-dark text-white py-3">
      <h5 class="mb-0 text-uppercase small fw-bold">
        <i class="bi bi-robot me-2"></i> Análisis Inteligente
      </h5>
    </div>
    <div class="card-body bg-light">
      <p class="card-text fs-5 lh-base" style="white-space: pre-wrap;">
        {{ content }}
      </p>
    </div>
  </div>
</template>