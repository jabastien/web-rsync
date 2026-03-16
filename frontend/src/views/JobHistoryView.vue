<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useJobsStore } from "../stores/jobs";
import LogViewer from "../components/LogViewer.vue";

const store = useJobsStore();
const route = useRoute();
const selectedRun = ref<number | null>(route.params.id ? Number(route.params.id) : null);

onMounted(() => store.fetchAll());

function statusClass(s: string) {
  return `badge badge-${s}`;
}

function select(id: number) {
  selectedRun.value = id;
}

</script>

<template>
  <div class="page">
    <h1 class="page-title">Job History</h1>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div class="card" style="padding:0;overflow:hidden">
        <table>
          <thead>
            <tr><th>ID</th><th>Task</th><th>Trigger</th><th>Status</th><th>Started</th></tr>
          </thead>
          <tbody>
            <tr v-for="run in store.runs" :key="run.id"
              :style="{ cursor:'pointer', background: selectedRun===run.id ? '#eff6ff' : '' }"
              @click="select(run.id)">
              <td>{{ run.id }}</td>
              <td>{{ run.task_id }}</td>
              <td>{{ run.trigger }}</td>
              <td><span :class="statusClass(run.status)">{{ run.status }}</span></td>
              <td>{{ new Date(run.started_at).toLocaleString() }}</td>
            </tr>
            <tr v-if="store.runs.length === 0">
              <td colspan="5" style="text-align:center;color:#9ca3af;padding:24px">No runs yet</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div>
        <div class="card" v-if="selectedRun">
          <h3 style="margin-top:0;font-size:14px">Log — Run #{{ selectedRun }}</h3>
          <LogViewer :key="selectedRun" :runId="selectedRun"
            :live="store.runs.find(r=>r.id===selectedRun)?.status === 'running'" />
        </div>
        <div class="card" v-else style="color:#9ca3af;text-align:center;padding:40px">
          Select a run to view its log
        </div>
      </div>
    </div>
  </div>
</template>
