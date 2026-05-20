<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { useJobsStore } from "../stores/jobs";
import LogViewer from "../components/LogViewer.vue";
import ConfirmModal from "../components/ConfirmModal.vue";

const store = useJobsStore();
const route = useRoute();
const selectedRun = ref<number | null>(route.params.id ? Number(route.params.id) : null);
const showPurgeConfirm = ref(false);
const loaded = ref(false);

const completedCount = computed(() => store.runs.filter(r => r.status !== "running").length);
const hasRunning = computed(() => store.runs.some(r => r.status === "running"));
const selectedStatus = computed(() => store.runs.find(r => r.id === selectedRun.value)?.status ?? null);

let pollTimer: ReturnType<typeof setInterval> | null = null;

function startPolling() {
  if (pollTimer !== null) return;
  pollTimer = setInterval(() => store.fetchAll(), 3000);
}

function stopPolling() {
  if (pollTimer !== null) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

watch(hasRunning, (val) => { val ? startPolling() : stopPolling(); });

onMounted(async () => {
  await store.fetchAll();
  loaded.value = true;
  if (hasRunning.value) startPolling();
});

onUnmounted(() => stopPolling());

function statusClass(s: string) {
  return `badge badge-${s}`;
}

function select(id: number) {
  selectedRun.value = id;
}

async function onRunDone() {
  await store.fetchAll();
}

async function confirmPurge() {
  await store.purge();
  showPurgeConfirm.value = false;
  if (selectedRun.value !== null && !store.runs.some(r => r.id === selectedRun.value)) {
    selectedRun.value = null;
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title" style="margin:0">Job History</h1>
      <button
        class="btn-danger"
        :disabled="completedCount === 0"
        @click="showPurgeConfirm = true"
      >
        <span class="mdi mdi-delete-sweep-outline"></span>Purge History
      </button>
    </div>

    <div class="history-layout">
      <div class="card" style="padding:0;overflow:hidden">
        <div class="table-responsive">
          <table>
            <thead>
              <tr><th>ID</th><th>Task</th><th>Trigger</th><th>Status</th><th>Started</th></tr>
            </thead>
            <tbody>
              <tr v-for="run in store.runs" :key="run.id"
                class="run-row"
                :class="{ 'run-selected': selectedRun === run.id }"
                @click="select(run.id)">
                <td>{{ run.id }}</td>
                <td>{{ run.task_id }}</td>
                <td>{{ run.trigger }}</td>
                <td><span :class="statusClass(run.status)">{{ run.status }}</span></td>
                <td>{{ new Date(run.started_at).toLocaleString() }}</td>
              </tr>
              <tr v-if="store.runs.length === 0">
                <td colspan="5" class="empty-row">No runs yet</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <div class="card" v-if="selectedRun && loaded">
          <h3 class="log-heading">
            <span class="mdi mdi-text-box-outline"></span>
            Log — Run #{{ selectedRun }}
            <span v-if="selectedStatus" :class="`badge badge-${selectedStatus}`" style="margin-left:8px;font-weight:400;font-size:11px">{{ selectedStatus }}</span>
          </h3>
          <LogViewer
            :key="selectedRun"
            :runId="selectedRun"
            :live="selectedStatus === 'running'"
            @done="onRunDone"
          />
        </div>
        <div class="card placeholder-card" v-else-if="!loaded">
          <span class="mdi mdi-loading mdi-spin"></span> Loading…
        </div>
        <div class="card placeholder-card" v-else>
          <span class="mdi mdi-cursor-default-click-outline"></span>
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

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.history-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.run-row { cursor: pointer; }
.run-selected td { background: var(--row-selected) !important; }

.log-heading {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-strong);
  display: flex;
  align-items: center;
  gap: 6px;
}
.log-heading .mdi { font-size: 16px; color: var(--text-muted); }

.empty-row {
  text-align: center;
  color: var(--text-faint);
  padding: 24px;
}

.placeholder-card {
  color: var(--text-faint);
  text-align: center;
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.placeholder-card .mdi { font-size: 28px; }

@media (max-width: 900px) {
  .history-layout {
    grid-template-columns: 1fr;
  }
}
</style>
