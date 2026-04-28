<script setup>
import { ref, onMounted } from 'vue';
import api from '@/services/api';

const selectedFile = ref(null);
const isUploading = ref(false);
const fileInput = ref(null);
const selectedFolder = ref('General');
const newFolderName = ref('');
const isCreatingFolder = ref(false);
const createFolderMode = ref(false);
const showUploadModal = ref(false);

const onFileSelected = (event) => {
  selectedFile.value = event.target.files[0];
};

const openUploadModal = () => {
  showUploadModal.value = true;
};

const closeUploadModal = () => {
  showUploadModal.value = false;
  resetUploadForm();
};

const resetUploadForm = () => {
  selectedFile.value = null;
  selectedFolder.value = 'General';
  newFolderName.value = '';
  createFolderMode.value = false;
  if (fileInput.value) fileInput.value.value = '';
};

const uploadFile = async () => {
  if (!selectedFile.value) {
    alert('Por favor, selecciona un archivo.');
    return;
  }

  isUploading.value = true;
  try {
    await api.uploadFile(selectedFile.value, selectedFolder.value);
    await fetchFiles();
    closeUploadModal();
    alert('¡Archivo subido con éxito!');
  } catch (error) {
    alert('Error al subir el archivo.');
  } finally {
    isUploading.value = false;
  }
};

const toggleCreateFolderMode = () => {
  createFolderMode.value = !createFolderMode.value;
  newFolderName.value = '';
};

const createNewFolder = async () => {
  if (!newFolderName.value.trim()) {
    alert('Por favor, ingresa un nombre para la carpeta.');
    return;
  }

  isCreatingFolder.value = true;
  try {
    await api.createFolder(newFolderName.value);
    await fetchFolders(); // Actualizar lista de carpetas
    selectedFolder.value = newFolderName.value;
    newFolderName.value = '';
    createFolderMode.value = false;
    alert('¡Carpeta creada con éxito!');
  } catch (error) {
    alert('Error al crear la carpeta.');
  } finally {
    isCreatingFolder.value = false;
  }
};

// List directories and CVs
const fileTree = ref({});
const folderList = ref([]);

const fetchFolders = async () => {
  try {
    folderList.value = await api.getFolders();
  } catch (error) {
    console.error('Error al obtener carpetas:', error);
  }
};

const fetchFiles = async () => {
  const data = await api.listFiles();
  fileTree.value = data;
};

const slugify = (text) => {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w-]+/g, '');
};

const openPDF = (folder, file) => {
  const relativePath = folder === 'General' ? file : `${folder}/${file}`;

  const encodedPath = relativePath
    .split('/')
    .map((part) => encodeURIComponent(part))
    .join('/');

  const url = `${api.baseURL}/pdfs/${encodedPath}`;
  window.open(url, '_blank');
};

onMounted(() => {
  fetchFolders();
  fetchFiles();
});
</script>

<template>
  <div class="container mt-4">
    <div class="row">
      <div class="col-12">
        <h3 class="mb-4"><i class="bi bi-file-earmark-pdf"></i> Gestión de Candidatos</h3>

        <div class="card shadow-sm mb-3">
          <div class="card-header bg-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0 px-2 py-1">Explorador de Candidatos</h5>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-primary" @click="openUploadModal">
                <i class="bi bi-cloud-arrow-up"></i> Subir
              </button>
              <button class="btn btn-sm btn-outline-secondary" @click="fetchFiles">
                <i class="bi bi-arrow-clockwise"></i> Actualizar
              </button>
            </div>
          </div>
          <div class="accordion accordion-flush shadow-sm border rounded" id="cvAccordion">
            <div class="accordion-item" v-for="(pdfList, folderName) in fileTree" :key="folderName">
              <h2 class="accordion-header">
                <button
                  class="accordion-button collapsed"
                  type="button"
                  data-bs-toggle="collapse"
                  :data-bs-target="'#id-' + slugify(folderName)"
                >
                  <i class="bi bi-folder-fill me-2 text-warning"></i>
                  {{ folderName }}
                </button>
              </h2>

              <div :id="'id-' + slugify(folderName)" class="accordion-collapse collapse">
                <div class="accordion-body p-0">
                  <ul class="list-group list-group-flush">
                    <li
                      v-for="pdfName in pdfList"
                      :key="pdfName"
                      class="list-group-item d-flex justify-content-between align-items-center py-2 px-4"
                    >
                      <div class="d-flex align-items-center">
                        <i class="bi bi-file-earmark-pdf text-danger me-3 fs-5"></i>
                        <span class="text-dark">{{ pdfName }}</span>
                      </div>
                      <button
                        class="btn btn-sm btn-outline-primary rounded-pill px-3"
                        @click="openPDF(folderName, pdfName)"
                      >
                        <i class="bi bi-eye me-1"></i> Ver
                      </button>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Subida -->
    <div
      v-if="showUploadModal"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      style="background-color: rgba(0, 0, 0, 0.5)"
    >
      <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-cloud-arrow-up me-2"></i>Subir Currículum</h5>
            <button
              type="button"
              class="btn-close"
              aria-label="Close"
              @click="closeUploadModal"
              :disabled="isUploading || isCreatingFolder"
            ></button>
          </div>

          <div class="modal-body">
            <!-- Selector de carpeta -->
            <div class="mb-3">
              <label class="form-label"><i class="bi bi-folder"></i> Carpeta de destino</label>
              <div class="d-flex gap-2">
                <select
                  v-if="!createFolderMode"
                  v-model="selectedFolder"
                  class="form-select"
                  :disabled="isUploading || isCreatingFolder"
                >
                  <option v-for="folder in folderList" :key="folder" :value="folder">
                    {{ folder }}
                  </option>
                </select>
                <input
                  v-else
                  v-model="newFolderName"
                  type="text"
                  class="form-control"
                  placeholder="Nombre de la nueva carpeta"
                  :disabled="isCreatingFolder"
                />
                <button
                  class="btn btn-outline-secondary"
                  type="button"
                  @click="toggleCreateFolderMode"
                  :disabled="isUploading || isCreatingFolder"
                >
                  <i :class="createFolderMode ? 'bi bi-x-lg' : 'bi bi-plus-lg'"></i>
                </button>
                <button
                  v-if="createFolderMode"
                  class="btn btn-success"
                  type="button"
                  @click="createNewFolder"
                  :disabled="isCreatingFolder"
                >
                  <span
                    v-if="isCreatingFolder"
                    class="spinner-border spinner-border-sm me-2"
                  ></span>
                  <i v-else class="bi bi-check-lg me-1"></i>Crear
                </button>
              </div>
            </div>

            <!-- Input de archivo -->
            <div class="mb-3">
              <label class="form-label"><i class="bi bi-file-pdf"></i> Seleccionar archivo</label>
              <input
                type="file"
                class="form-control"
                ref="fileInput"
                accept=".pdf"
                @change="onFileSelected"
                :disabled="isUploading || isCreatingFolder"
              />
              <small class="text-muted d-block mt-2">Solo archivos PDF. Máximo 10MB.</small>
              <div v-if="selectedFile" class="alert alert-info mt-2 mb-0">
                <i class="bi bi-info-circle me-2"></i>
                <strong>Archivo seleccionado:</strong> {{ selectedFile.name }}
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeUploadModal"
              :disabled="isUploading || isCreatingFolder"
            >
              Cancelar
            </button>
            <button
              type="button"
              class="btn btn-primary"
              @click="uploadFile"
              :disabled="!selectedFile || isUploading || isCreatingFolder"
            >
              <span v-if="isUploading" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="bi bi-upload me-1"></i>
              {{ isUploading ? 'Subiendo...' : 'Subir' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
