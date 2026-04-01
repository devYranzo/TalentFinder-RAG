import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

// Opción recomendada: Exportar un objeto con las funciones
export default {
  async getStatus() {
    const response = await apiClient.get('/status');
    return response.data;
  },

  async startIngest() {
    const response = await apiClient.post('/ingest');
    return response.data;
  },

  buscarCandidatos(query) {
    return apiClient.get('/search', { params: { q: query } });
  },

  ingresarDocumentos() {
    return apiClient.post('/ingest');
  },
};
