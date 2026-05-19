<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useHostsStore } from "../stores/hosts";
import { getSshKeys, deployKey } from "../api/client";

const store = useHostsStore();
const publicKey = ref("");
const deployModal = ref<{ hostId: number; password: string } | null>(null);
const deployError = ref("");

onMounted(async () => {
  await store.fetchAll();
  const keys = (await getSshKeys()).data;
  if (keys.length) publicKey.value = keys[0].public_key;
});

function openDeploy(hostId: number) {
  deployModal.value = { hostId, password: "" };
  deployError.value = "";
}

async function submitDeploy() {
  if (!deployModal.value) return;
  try {
    await deployKey(deployModal.value.hostId, deployModal.value.password);
    deployModal.value = null;
    alert("Key deployed successfully!");
  } catch (e: any) {
    deployError.value = e.response?.data?.detail ?? e.message;
  }
}
</script>

<template>
  <div class="page">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h1 class="page-title" style="margin:0">Hosts</h1>
      <RouterLink to="/hosts/new"><button class="btn-primary">+ New Host</button></RouterLink>
    </div>

    <div class="card" v-if="publicKey">
      <strong>Server Public Key</strong>
      <pre style="background:#f3f4f6;padding:10px;border-radius:4px;font-size:11px;overflow-x:auto;margin:8px 0 0">{{ publicKey }}</pre>
    </div>

    <div class="card" style="padding:0">
      <table>
        <colgroup>
          <col class="col-name">
          <col class="col-hostname">
          <col class="col-port">
          <col class="col-user">
        </colgroup>
        <thead>
          <tr><th>Name</th><th>Hostname</th><th>Port</th><th>User</th></tr>
        </thead>
        <tbody>
          <template v-for="host in store.hosts" :key="host.id">
            <tr class="data-row">
              <td><strong>{{ host.name }}</strong></td>
              <td class="truncate-cell">{{ host.hostname }}</td>
              <td>{{ host.port }}</td>
              <td>{{ host.username }}</td>
            </tr>
            <tr class="actions-row">
              <td colspan="4">
                <button class="btn-secondary btn-sm" @click="openDeploy(host.id)">Deploy Key</button>
                <RouterLink :to="`/hosts/${host.id}/edit`">
                  <button class="btn-secondary btn-sm">Edit</button>
                </RouterLink>
                <button class="btn-danger btn-sm" @click="store.remove(host.id)">Del</button>
              </td>
            </tr>
          </template>
          <tr v-if="store.hosts.length === 0">
            <td colspan="4" style="text-align:center;color:#9ca3af;padding:24px">
              No hosts yet. <RouterLink to="/hosts/new">Add one</RouterLink>.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Deploy Key Modal -->
    <div v-if="deployModal" class="modal-overlay" @click.self="deployModal=null">
      <div class="card" style="width:380px;margin:auto">
        <h3 style="margin-top:0">Deploy SSH Key</h3>
        <p style="color:#6b7280;font-size:13px">
          Enter the SSH password to add the server's public key to authorized_keys.
        </p>
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="deployModal.password" @keyup.enter="submitDeploy" autofocus />
        </div>
        <p v-if="deployError" style="color:red">{{ deployError }}</p>
        <div style="display:flex;gap:8px">
          <button class="btn-primary" @click="submitDeploy">Deploy</button>
          <button class="btn-secondary" @click="deployModal=null">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.col-name     { width: 20%; }
.col-hostname { width: 45%; }
.col-port     { width: 10%; }
.col-user     { width: 25%; }

.truncate-cell {
  max-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.data-row td { border-bottom: none; }

.actions-row td {
  padding-top: 2px;
  padding-bottom: 8px;
}

.actions-row button,
.actions-row a { margin-right: 4px; }

.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
</style>
