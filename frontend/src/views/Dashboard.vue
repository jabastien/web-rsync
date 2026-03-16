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

    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px">
      <div class="card" style="text-align:center">
        <div style="font-size:32px;font-weight:700">{{ tasksStore.tasks.length }}</div>
        <div style="color:#6b7280">Tasks</div>
      </div>
      <div class="card" style="text-align:center">
        <div style="font-size:32px;font-weight:700">{{ schedulerJobs.length }}</div>
        <div style="color:#6b7280">Scheduled Jobs</div>
      </div>
      <div class="card" style="text-align:center">
        <div style="font-size:32px;font-weight:700">{{ jobsStore.runs.filter(r=>r.status==='running').length }}</div>
        <div style="color:#6b7280">Running Now</div>
      </div>
    </div>

    <div class="card">
      <h2 style="margin-top:0;font-size:15px">Recent Runs</h2>
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
            <td colspan="5" style="text-align:center;color:#9ca3af">No runs yet</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card" v-if="schedulerJobs.length">
      <h2 style="margin-top:0;font-size:15px">Upcoming Scheduled Jobs</h2>
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
</template>
