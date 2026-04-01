import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://192.168.20.140:8000',
  headers: { 'Content-Type': 'application/json' },
});

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

  getPdfUrl(ruta) {
    const rutaLimpia = ruta.replace(/^CVs\//, '');
    return `${apiClient.defaults.baseURL}/pdfs/${rutaLimpia}`;
  },
};
