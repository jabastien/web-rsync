<script setup lang="ts">
declare const __APP_VERSION__: string;
const version = __APP_VERSION__;
</script>

<template>
  <nav class="sidebar">
    <div class="sidebar-brand">web-RSync</div>
    <div class="sidebar-nav">
      <RouterLink to="/">Dashboard</RouterLink>
      <RouterLink to="/tasks">Tasks</RouterLink>
      <RouterLink to="/hosts">Hosts</RouterLink>
      <RouterLink to="/history">History</RouterLink>
      <RouterLink to="/help">Help</RouterLink>
    </div>
    <div class="sidebar-footer">v{{ version }}</div>
  </nav>
  <RouterView />
</template>

<style scoped>
.sidebar {
  width: 180px;
  background: #1e293b;
  color: #cbd5e1;
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  flex-shrink: 0;
}
.sidebar-brand {
  font-size: 16px;
  font-weight: 700;
  color: #f8fafc;
  padding: 0 16px 20px;
  letter-spacing: 0.03em;
}
.sidebar-nav {
  flex: 1;
}
.sidebar a {
  display: block;
  padding: 10px 16px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  border-radius: 0;
}
.sidebar a:hover, .sidebar a.router-link-active {
  background: #334155;
  color: #f1f5f9;
}
.sidebar-footer {
  padding: 12px 16px 4px;
  font-size: 11px;
  color: #475569;
  border-top: 1px solid #334155;
  margin-top: 8px;
}
</style>
