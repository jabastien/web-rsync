<template>
  <nav class="sidebar">
    <div class="sidebar-brand">web-RSync</div>
    <RouterLink to="/">Dashboard</RouterLink>
    <RouterLink to="/tasks">Tasks</RouterLink>
    <RouterLink to="/hosts">Hosts</RouterLink>
    <RouterLink to="/history">History</RouterLink>
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
</style>
