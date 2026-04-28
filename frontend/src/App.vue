<script setup lang="ts">
import Header from './components/Header.vue';
import { useMotorStatus } from '@/composables/useMotorStatus';
import { useTheme } from '@/composables/useTheme';

const { isReady, encenderMotor, reindexar } = useMotorStatus();
const { isDark, toggleTheme } = useTheme();
</script>

<template>
  <main class="container">
    <Header
      :is-ready="isReady"
      :is-dark="isDark"
      @encender="encenderMotor"
      @reindexar="reindexar"
      @toggle-theme="toggleTheme"
    />
    <router-view />
  </main>
</template>

<style>
.container {
  max-width: 1100px;
}
/* Estilo para saber qué link está activo */
.router-link-active {
  color: #fff !important;
  font-weight: bold;
}
</style>
