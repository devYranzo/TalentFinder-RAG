import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 50000,
});

export default {
  baseURL: BASE_URL,

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
    const response = await apiClient.post('/query', { question: query });

    return response;
  },

  getPdfUrl(ruta) {
    const rutaLimpia = ruta.replace(/^CVs\//, '');
    return `${apiClient.defaults.baseURL}/pdfs/${rutaLimpia}`;
  },

  async listFiles() {
    const response = await apiClient.get('/filemanager/list');
    return response.data;
  },

  async getFolders() {
    const response = await apiClient.get('/filemanager/folders');
    return response.data.folders;
  },

  async uploadFile(file, folder = 'General') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder', folder);
    const response = await apiClient.post('/filemanager/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async createFolder(folderName) {
    const formData = new FormData();
    formData.append('folder_name', folderName);
    const response = await apiClient.post('/filemanager/create-folder', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
