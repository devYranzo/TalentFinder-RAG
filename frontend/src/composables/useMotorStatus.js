import { ref, computed, onMounted, onUnmounted } from 'vue';
import api from '@/services/api';

export function useMotorStatus() {
  const motorStatus = ref({
    is_ready: false,
    total_vectors: 0,
    total_files: 0,
    is_indexing: false,
  });
  const loadingIngest = ref(false);
  const progreso = ref(0);

  let statusInterval = null;

  const isReady = computed(() => motorStatus.value.is_ready || motorStatus.value.total_vectors > 0);

  const checkStatus = async () => {
    try {
      const data = await api.getStatus();
      motorStatus.value = data;

      if (data.is_indexing) {
        loadingIngest.value = true;
        if (data.total_documents > 0) {
          const porcentajeReal = Math.round(
            (data.processed_documents / data.total_documents) * 100
          );
          progreso.value = Math.min(porcentajeReal, 99);
        }
      } else {
        if (loadingIngest.value) {
          progreso.value = 100;
          setTimeout(() => {
            loadingIngest.value = false;
            motorStatus.value.is_ready = true;
          }, 1500);
        }
        detenerIntervalo();
      }
    } catch (e) {
      console.error('Error en polling:', e);
    }
  };

  const iniciarIntervalo = () => {
    if (!statusInterval) {
      statusInterval = setInterval(checkStatus, 2500);
    }
  };

  const detenerIntervalo = () => {
    if (statusInterval) {
      clearInterval(statusInterval);
      statusInterval = null;
    }
  };

  const encenderMotor = async () => {
    if (loadingIngest.value) return;
    loadingIngest.value = true;
    progreso.value = 0;
    try {
      await api.startIngest();
      iniciarIntervalo();
    } catch (error) {
      loadingIngest.value = false;
      alert('No se pudo iniciar el proceso de ingesta.');
    }
  };

  onMounted(async () => {
    await checkStatus();
    if (motorStatus.value.is_indexing) {
      iniciarIntervalo();
    }
  });

  onUnmounted(() => {
    detenerIntervalo();
  });

  return {
    motorStatus,
    loadingIngest,
    progreso,
    isReady,
    encenderMotor,
  };
}
