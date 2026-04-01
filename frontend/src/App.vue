<script setup>
import Header from './components/Header.vue';
import IngestProgress from './components/IngestProgress.vue';
import SearchBar from './components/SearchBar.vue';
import ResultCard from './components/ResultCard.vue';

import { useMotorStatus } from './composables/useMotorStatus';
import { useSearch } from './composables/useSearch';

// --- Composables ---
const { isReady, loadingIngest, progreso, encenderMotor } = useMotorStatus();
const { query, respuesta, loading, copiado, canSearch, buscar, copiarAlPortapapeles } =
  useSearch(isReady);
</script>

<template>
  <div class="container pt-5">
    <Header :is-ready="isReady" :loading-ingest="loadingIngest" @encender="encenderMotor" />

    <IngestProgress v-if="loadingIngest" :progreso="progreso" />

    <SearchBar
      v-model="query"
      :is-ready="isReady"
      :loading="loading"
      :can-search="canSearch"
      @buscar="buscar"
    />

    <ResultCard :respuesta="respuesta" :copiado="copiado" @copiar="copiarAlPortapapeles" />
  </div>
</template>

<style>
.container {
  max-width: 1100px;
}
</style>
