<script setup>
import IngestProgress from '@/components/IngestProgress.vue';
import SearchBar from '@/components/SearchBar.vue';
import ResultCard from '@/components/ResultCard.vue';
import { useSearch } from '@/composables/useSearch';
import { useMotorStatus } from '@/composables/useMotorStatus';

const { isReady, loadingIngest } = useMotorStatus();

const { query, respuesta, loading, copiado, canSearch, buscar, copiarAlPortapapeles } =
  useSearch(isReady);
</script>

<template>
  <div>
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
