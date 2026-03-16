import { defineStore } from "pinia";
import { ref } from "vue";
import * as api from "../api/client";

export interface Host {
  id: number;
  name: string;
  hostname: string;
  port: number;
  username: string;
  ssh_key_path: string | null;
  created_at: string;
  updated_at: string;
}

export const useHostsStore = defineStore("hosts", () => {
  const hosts = ref<Host[]>([]);

  async function fetchAll() {
    hosts.value = (await api.getHosts()).data;
  }

  async function remove(id: number) {
    await api.deleteHost(id);
    hosts.value = hosts.value.filter((h) => h.id !== id);
  }

  return { hosts, fetchAll, remove };
});
