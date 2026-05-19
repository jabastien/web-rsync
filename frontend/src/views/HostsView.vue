<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useHostsStore } from "../stores/hosts";
import { getSshKeys, deployKey } from "../api/client";
import ConfirmModal from "../components/ConfirmModal.vue";

const store = useHostsStore();
const publicKey = ref("");
const deployModal = ref<{ hostId: number; password: string } | null>(null);
const deployError = ref("");
const deploySuccess = ref(false);
const pendingDelete = ref<{ id: number; name: string } | null>(null);

onMounted(async () => {
  await store.fetchAll();
  const keys = (await getSshKeys()).data;
  if (keys.length) publicKey.value = keys[0].public_key;
});

function openDeploy(hostId: number) {
  deployModal.value = { hostId, password: "" };
  deployError.value = "";
  deploySuccess.value = false;
}

function closeDeploy() {
  deployModal.value = null;
  deploySuccess.value = false;
  deployError.value = "";
}

async function submitDeploy() {
  if (!deployModal.value) return;
  deployError.value = "";
  try {
    await deployKey(deployModal.value.hostId, deployModal.value.password);
    deploySuccess.value = true;
  } catch (e: any) {
    deployError.value = e.response?.data?.detail ?? e.message;
  }
}
async function confirmDelete() {
  if (!pendingDelete.value) return;
  await store.remove(pendingDelete.value.id);
  pendingDelete.value = null;
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
                <button class="btn-danger btn-sm" @click="pendingDelete = { id: host.id, name: host.name }">Del</button>
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
    <div v-if="deployModal" class="modal-overlay" @click.self="closeDeploy">
      <div class="card" style="width:380px;margin:auto">
        <!-- Success state -->
        <template v-if="deploySuccess">
          <div class="deploy-success">
            <span class="deploy-success-icon">✓</span>
            <h3 class="deploy-success-title">Key deployed successfully</h3>
            <p class="deploy-success-msg">
              The server's public key has been added to <code>~/.ssh/authorized_keys</code>
              on the remote host. rsync tasks to this host will now authenticate without a password.
            </p>
          </div>
          <button class="btn-primary" @click="closeDeploy">Close</button>
        </template>

        <!-- Form state -->
        <template v-else>
          <h3 style="margin-top:0">Deploy SSH Key</h3>
          <p style="color:#6b7280;font-size:13px">
            Enter the SSH password to add the server's public key to authorized_keys.
          </p>
          <div class="form-group">
            <label>Password</label>
            <input type="password" v-model="deployModal.password" @keyup.enter="submitDeploy" autofocus />
          </div>
          <p v-if="deployError" class="deploy-error">{{ deployError }}</p>
          <div style="display:flex;gap:8px">
            <button class="btn-primary" @click="submitDeploy">Deploy</button>
            <button class="btn-secondary" @click="closeDeploy">Cancel</button>
          </div>
        </template>
      </div>
    </div>
  </div>

  <ConfirmModal
    v-if="pendingDelete"
    title="Delete Host"
    :message="`Delete host '${pendingDelete.name}'? This cannot be undone.`"
    @confirm="confirmDelete"
    @cancel="pendingDelete = null"
  />
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

.deploy-success {
  text-align: center;
  padding: 8px 0 20px;
}
.deploy-success-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #dcfce7;
  color: #16a34a;
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 12px;
}
.deploy-success-title {
  margin: 0 0 8px;
  font-size: 15px;
  color: #111827;
}
.deploy-success-msg {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  margin: 0;
}

.deploy-error {
  color: #dc2626;
  font-size: 13px;
  margin: 8px 0 0;
}
</style>
