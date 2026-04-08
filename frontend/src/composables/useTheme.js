import { ref, watch, onMounted } from 'vue';

export function useTheme() {
  const isDark = ref(false);

  const initTheme = () => {
    // Check localStorage for saved preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      isDark.value = savedTheme === 'dark';
    } else {
      // Default to system preference
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    applyTheme();
  };

  const applyTheme = () => {
    const html = document.documentElement;
    if (isDark.value) {
      html.setAttribute('data-bs-theme', 'dark');
      document.body.style.backgroundColor = '#1a1a1a';
      document.body.style.color = '#ffffff';
    } else {
      html.removeAttribute('data-bs-theme');
      document.body.style.backgroundColor = '#ffffff';
      document.body.style.color = '#000000';
    }
  };

  const toggleTheme = () => {
    isDark.value = !isDark.value;
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light');
    applyTheme();
  };

  watch(isDark, () => {
    applyTheme();
  });

  onMounted(() => {
    initTheme();
  });

  return {
    isDark,
    toggleTheme,
    initTheme,
  };
}
