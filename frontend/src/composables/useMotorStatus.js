import { ref, computed, onMounted, onUnmounted } from 'vue';
import api from '@/services/api';

export function useMotorStatus() {
  const motorStatus = ref({
    is_ready: false,
    is_indexing: false,
    processed: 0,
    total: 0,
    progress_percent: 0,
    error: null,
  });

  const loadingIngest = ref(false);
  const progreso = ref(0);
  let statusInterval = null;

  // El motor está listo si NO está indexando y ya hay documentos procesados
  const isReady = computed(() => !motorStatus.value.is_indexing && motorStatus.value.total > 0);

  const checkStatus = async () => {
    try {
      const data = await api.getStatus();

      // Actualizamos el estado con la respuesta del backend
      motorStatus.value = {
        ...motorStatus.value,
        ...data,
      };

      if (data.is_indexing) {
        loadingIngest.value = true;
        // Sincronizamos el progreso con el porcentaje que envía el backend
        progreso.value = Math.min(data.progress_percent || 0, 99);
      } else {
        // Si estaba cargando y el backend dice que ya terminó
        if (loadingIngest.value) {
          progreso.value = 100;
          setTimeout(() => {
            loadingIngest.value = false;
            motorStatus.value.is_ready = true;
          }, 1500);
        }
        // Si no está indexando, detenemos el polling para ahorrar recursos
        detenerIntervalo();
      }
    } catch (e) {
      console.error('Error al obtener el estado del motor:', e);
    }
  };

  const iniciarIntervalo = () => {
    if (!statusInterval) {
      // Consultamos cada 2.5 segundos
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

  const reindexar = async () => {
    if (loadingIngest.value) return;

    const confirmacion = confirm(
      '⚠️ Esto eliminará todos los vectores existentes y volverá a indexar todos los CVs desde cero.\n\n¿Estás seguro de que deseas continuar?'
    );

    if (!confirmacion) return;

    loadingIngest.value = true;
    progreso.value = 0;
    motorStatus.value.is_ready = false;

    try {
      await api.reindex();
      iniciarIntervalo();
    } catch (error) {
      loadingIngest.value = false;
      alert('No se pudo iniciar el proceso de reindexación.');
    }
  };

  onMounted(async () => {
    // Al cargar el componente, comprobamos el estado inicial
    await checkStatus();
    // Si el motor ya estaba indexando, arrancamos el intervalo automáticamente
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
    reindexar,
    checkStatus, // Lo exponemos por si quieres un botón de "refrescar" manual
  };
}
