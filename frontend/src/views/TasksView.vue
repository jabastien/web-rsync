<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useTasksStore } from "../stores/tasks";
import { runTask, dryRunTask, cloneTask } from "../api/client";
import ScheduleBadge from "../components/ScheduleBadge.vue";

const store = useTasksStore();
const router = useRouter();

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
</script>

<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h1 class="page-title" style="margin:0">Tasks</h1>
      <RouterLink to="/tasks/new"><button class="btn-primary">+ New Task</button></RouterLink>
    </div>

    <div class="card" style="padding:0">
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Source</th><th>Destination</th>
            <th>Schedule</th><th>Enabled</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in store.tasks" :key="task.id">
            <td><strong>{{ task.name }}</strong></td>
            <td><code>{{ task.source_path }}</code></td>
            <td><code>{{ task.dest_path }}</code></td>
            <td><ScheduleBadge :schedule="task.schedule" /></td>
            <td>
              <input type="checkbox" :checked="task.enabled"
                @change="store.toggle(task.id, ($event.target as HTMLInputElement).checked)" />
            </td>
            <td style="white-space:nowrap">
              <button class="btn-primary btn-sm" @click="run(task.id)">Run</button>
              <button class="btn-secondary btn-sm" style="margin-left:4px" @click="dry(task.id)">Dry</button>
              <RouterLink :to="`/tasks/${task.id}/edit`">
                <button class="btn-secondary btn-sm" style="margin-left:4px">Edit</button>
              </RouterLink>
              <button class="btn-secondary btn-sm" style="margin-left:4px" @click="clone(task.id)">Clone</button>
              <button class="btn-danger btn-sm" style="margin-left:4px"
                @click="store.remove(task.id)">Del</button>
            </td>
          </tr>
          <tr v-if="store.tasks.length === 0">
            <td colspan="6" style="text-align:center;color:#9ca3af;padding:24px">
              No tasks yet. <RouterLink to="/tasks/new">Create one</RouterLink>.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
