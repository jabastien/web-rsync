<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useTheme } from "./composables/useTheme";

declare const __APP_VERSION__: string;
const version = __APP_VERSION__;

const { isDark, toggle } = useTheme();
const sidebarOpen = ref(false);
const route = useRoute();

watch(() => route.path, () => { sidebarOpen.value = false; });

const navItems = [
  { to: "/",        label: "Dashboard", icon: "mdi-view-dashboard-outline" },
  { to: "/tasks",   label: "Tasks",     icon: "mdi-sync"                   },
  { to: "/hosts",   label: "Hosts",     icon: "mdi-server-network"         },
  { to: "/history",       label: "History",       icon: "mdi-history"                },
  { to: "/notifications", label: "Notifications", icon: "mdi-bell-outline"           },
  { to: "/help",          label: "Help",          icon: "mdi-help-circle-outline"    },
];
</script>

<template>
  <!-- Mobile top bar -->
  <div class="mobile-topbar">
    <button class="topbar-hamburger" @click="sidebarOpen = !sidebarOpen" aria-label="Menu">
      <span class="mdi" :class="sidebarOpen ? 'mdi-close' : 'mdi-menu'"></span>
    </button>
    <span class="topbar-brand">
      <span class="mdi mdi-archive-sync"></span>
      web-RSync
    </span>
    <button class="topbar-theme-btn" @click="toggle" :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
      <span class="mdi" :class="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"></span>
    </button>
  </div>

  <!-- Sidebar backdrop (mobile only) -->
  <Transition name="fade">
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>
  </Transition>

  <!-- Sidebar -->
  <nav class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
    <div class="sidebar-brand">
      <span class="mdi mdi-archive-sync brand-icon"></span>
      web-RSync
    </div>

    <div class="sidebar-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        @click="sidebarOpen = false"
      >
        <span class="mdi" :class="item.icon"></span>
        {{ item.label }}
      </RouterLink>
    </div>

    <div class="sidebar-footer">
      <button class="theme-toggle" @click="toggle" :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
        <span class="mdi" :class="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"></span>
        <span class="toggle-label">{{ isDark ? "Light mode" : "Dark mode" }}</span>
      </button>
      <div class="sidebar-version">v{{ version }}</div>
    </div>
  </nav>

  <RouterView />
</template>

<style scoped>
/* ── Sidebar ── */
.sidebar {
  width: 200px;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: 1px solid var(--sidebar-border);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #f8fafc;
  padding: 18px 16px 16px;
  border-bottom: 1px solid var(--sidebar-border);
  letter-spacing: 0.02em;
}

.brand-icon {
  font-size: 22px;
  color: #60a5fa;
}

.sidebar-nav {
  flex: 1;
  padding-top: 6px;
}

.sidebar a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.12s, color 0.12s;
  border-left: 3px solid transparent;
}

.sidebar a .mdi {
  font-size: 18px;
  width: 20px;
  text-align: center;
}

.sidebar a:hover {
  background: var(--sidebar-hover);
  color: #f1f5f9;
  text-decoration: none;
}

.sidebar a.router-link-active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-active-text);
  border-left-color: var(--primary);
}

/* ── Sidebar footer ── */
.sidebar-footer {
  padding: 12px 16px 16px;
  border-top: 1px solid var(--sidebar-border);
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  background: none;
  border: none;
  color: var(--sidebar-text);
  padding: 6px 0;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.12s;
  border-radius: 0;
}

.theme-toggle:hover { color: #f1f5f9; }
.theme-toggle .mdi { font-size: 16px; }
.toggle-label { flex: 1; text-align: left; }

.sidebar-version {
  font-size: 11px;
  color: var(--text-faint);
  margin-top: 6px;
  padding-left: 2px;
}

/* ── Backdrop (mobile) ── */
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 49;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── Mobile overrides ── */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 52px;
    left: -220px;
    width: 200px;
    height: calc(100vh - 52px);
    z-index: 60;
    transition: left 0.22s ease;
    overflow-y: auto;
    padding-top: 4px;
  }
  .sidebar.sidebar-open { left: 0; }
  /* Brand is shown in the top bar on mobile */
  .sidebar-brand { display: none; }
}
</style>
