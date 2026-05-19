<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useJobsStore } from "../stores/jobs";
import LogViewer from "../components/LogViewer.vue";
import ConfirmModal from "../components/ConfirmModal.vue";

const store = useJobsStore();
const route = useRoute();
const selectedRun = ref<number | null>(route.params.id ? Number(route.params.id) : null);
const showPurgeConfirm = ref(false);

onMounted(() => store.fetchAll());

const completedCount = computed(() => store.runs.filter(r => r.status !== "running").length);

function statusClass(s: string) {
  return `badge badge-${s}`;
}

function select(id: number) {
  selectedRun.value = id;
}

async function confirmPurge() {
  await store.purge();
  showPurgeConfirm.value = false;
  if (selectedRun.value !== null) {
    const stillExists = store.runs.some(r => r.id === selectedRun.value);
    if (!stillExists) selectedRun.value = null;
  }
}
</script>

<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h1 class="page-title" style="margin:0">Job History</h1>
      <button
        class="btn-danger"
        :disabled="completedCount === 0"
        @click="showPurgeConfirm = true"
      >Purge History</button>
    </div>

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

  <ConfirmModal
    v-if="showPurgeConfirm"
    title="Purge Job History"
    :message="`Permanently delete ${completedCount} completed run${completedCount !== 1 ? 's' : ''} and their log files? Running jobs are not affected. This cannot be undone.`"
    confirmLabel="Purge"
    @confirm="confirmPurge"
    @cancel="showPurgeConfirm = false"
  />
</template>
