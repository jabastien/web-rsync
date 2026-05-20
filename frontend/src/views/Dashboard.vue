<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useTasksStore } from "../stores/tasks";
import { useJobsStore } from "../stores/jobs";
import { getSchedulerJobs } from "../api/client";

const tasksStore = useTasksStore();
const jobsStore = useJobsStore();
const schedulerJobs = ref<any[]>([]);

onMounted(async () => {
  await Promise.all([tasksStore.fetchAll(), jobsStore.fetchAll()]);
  schedulerJobs.value = (await getSchedulerJobs()).data;
});

function statusClass(s: string) {
  return `badge badge-${s}`;
}

const recentRuns = () => jobsStore.runs.slice(0, 5);
</script>

<template>
  <div class="page">
    <h1 class="page-title">Dashboard</h1>

    <div class="stats-grid">
      <div class="card stat-card">
        <span class="mdi mdi-sync stat-icon"></span>
        <div class="stat-value">{{ tasksStore.tasks.length }}</div>
        <div class="stat-label">Tasks</div>
      </div>
      <div class="card stat-card">
        <span class="mdi mdi-calendar-clock-outline stat-icon"></span>
        <div class="stat-value">{{ schedulerJobs.length }}</div>
        <div class="stat-label">Scheduled Jobs</div>
      </div>
      <div class="card stat-card">
        <span class="mdi mdi-play-circle-outline stat-icon running"></span>
        <div class="stat-value">{{ jobsStore.runs.filter(r=>r.status==='running').length }}</div>
        <div class="stat-label">Running Now</div>
      </div>
    </div>

    <div class="card">
      <h2 class="card-heading">Recent Runs</h2>
      <div class="table-responsive">
        <table>
          <thead>
            <tr><th>ID</th><th>Task</th><th>Trigger</th><th>Status</th><th>Started</th></tr>
          </thead>
          <tbody>
            <tr v-for="run in recentRuns()" :key="run.id">
              <td>{{ run.id }}</td>
              <td>{{ run.task_id }}</td>
              <td>{{ run.trigger }}</td>
              <td><span :class="statusClass(run.status)">{{ run.status }}</span></td>
              <td>{{ new Date(run.started_at).toLocaleString() }}</td>
            </tr>
            <tr v-if="jobsStore.runs.length === 0">
              <td colspan="5" class="empty-row">No runs yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card" v-if="schedulerJobs.length">
      <h2 class="card-heading">Upcoming Scheduled Jobs</h2>
      <div class="table-responsive">
        <table>
          <thead><tr><th>Job ID</th><th>Next Run</th><th>Trigger</th></tr></thead>
          <tbody>
            <tr v-for="j in schedulerJobs" :key="j.id">
              <td>{{ j.id }}</td>
              <td>{{ j.next_run ? new Date(j.next_run).toLocaleString() : "—" }}</td>
              <td>{{ j.trigger }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  padding: 20px 16px;
}

.stat-icon {
  font-size: 28px;
  color: var(--text-muted);
  display: block;
  margin-bottom: 8px;
}
.stat-icon.running { color: var(--badge-running-text); }

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-strong);
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label { color: var(--text-muted); font-size: 12px; }

.card-heading {
  margin-top: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-strong);
  margin-bottom: 12px;
}

.empty-row {
  text-align: center;
  color: var(--text-faint);
  padding: 24px;
}
</style>
