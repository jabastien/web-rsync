import { defineStore } from "pinia";
import { ref } from "vue";
import * as api from "../api/client";

export interface JobRun {
  id: number;
  task_id: number;
  trigger: string;
  started_at: string;
  finished_at: string | null;
  exit_code: number | null;
  status: string;
}

export const useJobsStore = defineStore("jobs", () => {
  const runs = ref<JobRun[]>([]);

  async function fetchAll(taskId?: number) {
    const params = taskId ? { task_id: taskId } : {};
    runs.value = (await api.getJobRuns(params)).data;
  }

  return { runs, fetchAll };
});
