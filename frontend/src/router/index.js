import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue';
import FileManager from '@/views/FileManager.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
  },
  {
    path: '/filemanager',
    name: 'File Manager',
    component: FileManager,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
