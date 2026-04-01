import { ref, computed } from 'vue';
import api from '@/services/api';

export function useSearch(isReady) {
  const query = ref('');
  const respuesta = ref('');
  const loading = ref(false);
  const copiado = ref(false);

  const canSearch = computed(
    () => isReady.value && !loading.value && query.value.trim().length > 0
  );

  const buscar = async () => {
    if (!canSearch.value) return;
    loading.value = true;
    respuesta.value = '';
    try {
      const res = await api.buscarCandidatos(query.value);
      respuesta.value = res.data.answer;
    } catch (error) {
      alert('Error en la búsqueda. El servidor podría estar saturado.');
    } finally {
      loading.value = false;
    }
  };

  const copiarAlPortapapeles = async () => {
    if (!respuesta.value) return;
    try {
      let textoLimpio = respuesta.value.replace(/\[BOTON_CV:.*?\]/g, '');
      textoLimpio = textoLimpio
        .replace(/###\s+/g, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/- /g, '• ')
        .trim();

      await navigator.clipboard.writeText(textoLimpio);
      copiado.value = true;
      setTimeout(() => {
        copiado.value = false;
      }, 2000);
    } catch (err) {
      console.error('Error al copiar:', err);
    }
  };

  return {
    query,
    respuesta,
    loading,
    copiado,
    canSearch,
    buscar,
    copiarAlPortapapeles,
  };
}
