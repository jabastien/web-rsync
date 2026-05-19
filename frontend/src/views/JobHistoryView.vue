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

// Poll every 3 s while any run is still running so status badges stay fresh
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
  await store.fetchAll();   // resolve before LogViewer mounts so `live` prop is correct
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

// Called by LogViewer when SSE stream closes — refresh to get final status
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
        <div class="card" v-if="selectedRun && loaded">
          <h3 style="margin-top:0;font-size:14px">
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
        <div class="card" v-else-if="!loaded" style="color:#9ca3af;text-align:center;padding:40px">
          Loading…
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
