import { defineStore } from "pinia";
import { ref } from "vue";
import * as api from "../api/client";

export interface Task {
  id: number;
  name: string;
  source_path: string;
  dest_path: string;
  rsync_options: string;
  schedule: string | null;
  enabled: boolean;
  notify_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export const useTasksStore = defineStore("tasks", () => {
  const tasks = ref<Task[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchAll() {
    loading.value = true;
    try {
      tasks.value = (await api.getTasks()).data;
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  async function toggle(id: number, enabled: boolean) {
    await api.toggleTask(id, enabled);
    const t = tasks.value.find((t) => t.id === id);
    if (t) t.enabled = enabled;
  }

  async function remove(id: number) {
    await api.deleteTask(id);
    tasks.value = tasks.value.filter((t) => t.id !== id);
  }

  return { tasks, loading, error, fetchAll, toggle, remove };
});
