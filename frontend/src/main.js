import { createApp } from 'vue';
import App from './App.vue';
import 'bootstrap-icons/font/bootstrap-icons.css';
import router from './router';

// Initialize theme on app load
const initializeTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  const isDark = savedTheme
    ? savedTheme === 'dark'
    : window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (isDark) {
    document.documentElement.setAttribute('data-bs-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-bs-theme');
  }
};

initializeTheme();

createApp(App).use(router).mount('#app');
