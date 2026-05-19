<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useTasksStore } from "../stores/tasks";
import { runTask, dryRunTask, cloneTask } from "../api/client";
import ScheduleBadge from "../components/ScheduleBadge.vue";
import ConfirmModal from "../components/ConfirmModal.vue";

const store = useTasksStore();
const router = useRouter();

const pendingDelete = ref<{ id: number; name: string } | null>(null);
const pathTooltip = ref<{ text: string; x: number; y: number } | null>(null);

function showPathTooltip(event: MouseEvent, text: string) {
  const el = event.currentTarget as HTMLElement;
  if (el.scrollWidth <= el.clientWidth) return;
  const r = el.getBoundingClientRect();
  pathTooltip.value = { text, x: r.left + window.scrollX, y: r.bottom + window.scrollY + 6 };
}

function hidePathTooltip() {
  pathTooltip.value = null;
}

onMounted(() => store.fetchAll());

async function run(id: number) {
  const res = await runTask(id);
  router.push(`/history/${res.data.run_id}`);
}
async function dry(id: number) {
  const res = await dryRunTask(id);
  router.push(`/history/${res.data.run_id}`);
}
async function clone(id: number) {
  await cloneTask(id);
  store.fetchAll();
}
async function confirmDelete() {
  if (!pendingDelete.value) return;
  await store.remove(pendingDelete.value.id);
  pendingDelete.value = null;
}
</script>

<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h1 class="page-title" style="margin:0">Tasks</h1>
      <RouterLink to="/tasks/new"><button class="btn-primary">+ New Task</button></RouterLink>
    </div>

    <div class="card" style="padding:0">
      <table>
        <colgroup>
          <col class="col-name">
          <col class="col-path">
          <col class="col-path">
          <col class="col-schedule">
          <col class="col-enabled">
        </colgroup>
        <thead>
          <tr>
            <th>Name</th><th>Source</th><th>Destination</th><th>Schedule</th><th>Enabled</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="task in store.tasks" :key="task.id">
            <tr class="data-row">
              <td><strong>{{ task.name }}</strong></td>
              <td class="path-cell"
                @mouseenter="showPathTooltip($event, task.source_path)"
                @mouseleave="hidePathTooltip"><code>{{ task.source_path }}</code></td>
              <td class="path-cell"
                @mouseenter="showPathTooltip($event, task.dest_path)"
                @mouseleave="hidePathTooltip"><code>{{ task.dest_path }}</code></td>
              <td><ScheduleBadge :schedule="task.schedule" /></td>
              <td>
                <input type="checkbox" :checked="task.enabled"
                  @change="store.toggle(task.id, ($event.target as HTMLInputElement).checked)" />
              </td>
            </tr>
            <tr class="actions-row">
              <td colspan="5">
                <button class="btn-primary btn-sm" @click="run(task.id)">Run</button>
                <button class="btn-secondary btn-sm" @click="dry(task.id)">Dry</button>
                <RouterLink :to="`/tasks/${task.id}/edit`">
                  <button class="btn-secondary btn-sm">Edit</button>
                </RouterLink>
                <button class="btn-secondary btn-sm" @click="clone(task.id)">Clone</button>
                <button class="btn-danger btn-sm" @click="pendingDelete = { id: task.id, name: task.name }">Del</button>
              </td>
            </tr>
          </template>
          <tr v-if="store.tasks.length === 0">
            <td colspan="5" style="text-align:center;color:#9ca3af;padding:24px">
              No tasks yet. <RouterLink to="/tasks/new">Create one</RouterLink>.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <ConfirmModal
    v-if="pendingDelete"
    title="Delete Task"
    :message="`Delete task '${pendingDelete.name}'? This cannot be undone.`"
    @confirm="confirmDelete"
    @cancel="pendingDelete = null"
  />

  <Teleport to="body">
    <div
      v-if="pathTooltip"
      class="path-tooltip"
      :style="{ top: pathTooltip.y + 'px', left: pathTooltip.x + 'px' }"
    >{{ pathTooltip.text }}</div>
  </Teleport>
</template>

<style scoped>
.col-name     { width: 15%; }
.col-path     { width: 32%; }
.col-schedule { width: 13%; }
.col-enabled  { width: 8%; }

.path-cell {
  max-width: 0;          /* lets the colgroup width drive truncation */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-row td { border-bottom: none; }

.actions-row td {
  padding-top: 2px;
  padding-bottom: 8px;
}

.actions-row button,
.actions-row a { margin-right: 4px; }
</style>

<style>
.path-tooltip {
  position: absolute;
  z-index: 9999;
  background: #1e293b;
  color: #f1f5f9;
  font-family: "Fira Code", "Cascadia Code", ui-monospace, monospace;
  font-size: 12px;
  padding: 5px 10px;
  border-radius: 5px;
  white-space: nowrap;
  pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,.25);
  max-width: min(640px, calc(100vw - 24px));
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
