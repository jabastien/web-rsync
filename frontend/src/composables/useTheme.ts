import { ref, computed, watchEffect } from "vue";

const STORAGE_KEY = "web-rsync-theme";
const theme = ref<"dark" | "light">(
  (localStorage.getItem(STORAGE_KEY) as "dark" | "light") ?? "dark"
);

watchEffect(() => {
  document.documentElement.setAttribute("data-theme", theme.value);
  localStorage.setItem(STORAGE_KEY, theme.value);
});

export function useTheme() {
  return {
    theme,
    isDark: computed(() => theme.value === "dark"),
    toggle() {
      theme.value = theme.value === "dark" ? "light" : "dark";
    },
  };
}
