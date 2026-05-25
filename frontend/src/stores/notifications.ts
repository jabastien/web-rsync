import { defineStore } from "pinia";
import { ref } from "vue";
import * as api from "../api/client";

export interface NotificationChannel {
  id: number;
  name: string;
  provider: "ntfy" | "gotify" | "discord" | "telegram" | "apprise" | "webhook";
  config: Record<string, any>;
  enabled: boolean;
  notify_on_success: boolean;
  notify_on_failure: boolean;
  created_at: string;
  updated_at: string;
}

export const useNotificationsStore = defineStore("notifications", () => {
  const channels = ref<NotificationChannel[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchAll() {
    loading.value = true;
    try {
      channels.value = (await api.getNotificationChannels()).data;
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  async function remove(id: number) {
    await api.deleteNotificationChannel(id);
    channels.value = channels.value.filter((c) => c.id !== id);
  }

  return { channels, loading, error, fetchAll, remove };
});
