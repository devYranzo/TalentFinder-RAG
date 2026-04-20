import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://192.168.20.208:8000',
  headers: { 'Content-Type': 'application/json' },
});

export default {
  async getStatus() {
    const response = await apiClient.get('/index/status');
    return response.data;
  },

  async startIngest() {
    const response = await apiClient.post('/index/start');
    return response.data;
  },

  async reindex() {
    const response = await apiClient.post('/index/reindex');
    return response.data;
  },

  async buscarCandidatos(query) {
    return apiClient.post('/query', { question: query });
  },

  async getPdfUrl(ruta) {
    const rutaLimpia = ruta.replace(/^CVs\//, '');
    return `${apiClient.defaults.baseURL}/pdfs/${rutaLimpia}`;
  },
};
