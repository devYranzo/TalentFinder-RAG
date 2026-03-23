<script setup>
import { ref } from 'vue';

const emit = defineEmits(['search']);

const queryText = ref('');

const emitSearch = () => {
  if (queryText.value.trim()) {
    emit('search', queryText.value);
  }
};
</script>

<template>
  <div class="input-group input-group-lg shadow-sm">
    <input 
      v-model="queryText" 
      @keyup.enter="emitSearch"
      type="text" 
      class="form-control" 
      placeholder="Ej: Experto en Python con AWS..."
    >
    <button @click="emitSearch" class="btn btn-primary px-4">
      <i class="bi bi-search"></i> Buscar
    </button>
  </div>
</template>