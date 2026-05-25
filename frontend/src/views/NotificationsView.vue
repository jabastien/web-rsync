<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { useNotificationsStore, type NotificationChannel } from "../stores/notifications";
import {
  createNotificationChannel,
  updateNotificationChannel,
  testNotificationChannel,
  deleteNotificationChannel,
} from "../api/client";
import ConfirmModal from "../components/ConfirmModal.vue";

const store = useNotificationsStore();
onMounted(() => store.fetchAll());

// ── form state ────────────────────────────────────────────────────────────────
const showForm = ref(false);
const editingId = ref<number | null>(null);

const EMPTY_FORM = () => ({
  name: "",
  provider: "ntfy" as NotificationChannel["provider"],
  enabled: true,
  notify_on_success: false,
  notify_on_failure: true,
  // ntfy
  ntfy_url: "https://ntfy.sh",
  ntfy_topic: "",
  ntfy_priority: "default",
  ntfy_token: "",
  // gotify
  gotify_url: "",
  gotify_token: "",
  gotify_priority: 5,
  // discord
  discord_webhook_url: "",
  // telegram
  tg_bot_token: "",
  tg_chat_id: "",
  // apprise (raw URL)
  apprise_url: "",
  // webhook
  wh_url: "",
  wh_headers: "{}",
  wh_body_template: "",
});

const form = reactive(EMPTY_FORM());

function openAdd() {
  Object.assign(form, EMPTY_FORM());
  editingId.value = null;
  showForm.value = true;
}

function openEdit(ch: NotificationChannel) {
  Object.assign(form, EMPTY_FORM());
  editingId.value = ch.id;
  form.name = ch.name;
  form.provider = ch.provider;
  form.enabled = ch.enabled;
  form.notify_on_success = ch.notify_on_success;
  form.notify_on_failure = ch.notify_on_failure;
  const cfg = ch.config;
  if (ch.provider === "ntfy") {
    form.ntfy_url = cfg.url ?? "https://ntfy.sh";
    form.ntfy_topic = cfg.topic ?? "";
    form.ntfy_priority = cfg.priority ?? "default";
    form.ntfy_token = cfg.token ?? "";
  } else if (ch.provider === "gotify") {
    form.gotify_url = cfg.url ?? "";
    form.gotify_token = cfg.token ?? "";
    form.gotify_priority = cfg.priority ?? 5;
  } else if (ch.provider === "discord") {
    form.discord_webhook_url = cfg.webhook_url ?? "";
  } else if (ch.provider === "telegram") {
    form.tg_bot_token = cfg.bot_token ?? "";
    form.tg_chat_id = cfg.chat_id ?? "";
  } else if (ch.provider === "apprise") {
    form.apprise_url = cfg.apprise_url ?? "";
  } else if (ch.provider === "webhook") {
    form.wh_url = cfg.url ?? "";
    form.wh_headers = JSON.stringify(cfg.headers ?? {}, null, 2);
    form.wh_body_template = cfg.body_template ?? "";
  }
  showForm.value = true;
}

function cancelForm() {
  showForm.value = false;
  editingId.value = null;
}

function buildConfig(): Record<string, any> {
  if (form.provider === "ntfy") {
    return { url: form.ntfy_url, topic: form.ntfy_topic, priority: form.ntfy_priority, token: form.ntfy_token };
  } else if (form.provider === "gotify") {
    return { url: form.gotify_url, token: form.gotify_token, priority: form.gotify_priority };
  } else if (form.provider === "discord") {
    return { webhook_url: form.discord_webhook_url };
  } else if (form.provider === "telegram") {
    return { bot_token: form.tg_bot_token, chat_id: form.tg_chat_id };
  } else if (form.provider === "apprise") {
    return { apprise_url: form.apprise_url };
  } else {
    let headers: Record<string, string> = {};
    try { headers = JSON.parse(form.wh_headers); } catch {}
    return { url: form.wh_url, headers, body_template: form.wh_body_template };
  }
}

const saveError = ref("");
async function submitForm() {
  saveError.value = "";
  const payload = {
    name: form.name,
    provider: form.provider,
    config: buildConfig(),
    enabled: form.enabled,
    notify_on_success: form.notify_on_success,
    notify_on_failure: form.notify_on_failure,
  };
  try {
    if (editingId.value !== null) {
      await updateNotificationChannel(editingId.value, payload);
    } else {
      await createNotificationChannel(payload);
    }
    await store.fetchAll();
    cancelForm();
  } catch (e: any) {
    saveError.value = e.response?.data?.detail ?? e.message;
  }
}

// ── test state ────────────────────────────────────────────────────────────────
const testState = ref<Record<number, "idle" | "loading" | "ok" | "error">>({});
const testError = ref<Record<number, string>>({});

async function runTest(id: number) {
  testState.value[id] = "loading";
  testError.value[id] = "";
  try {
    await testNotificationChannel(id);
    testState.value[id] = "ok";
  } catch (e: any) {
    testState.value[id] = "error";
    testError.value[id] = e.response?.data?.detail ?? e.message;
  }
  setTimeout(() => { testState.value[id] = "idle"; }, 4000);
}

// ── delete ────────────────────────────────────────────────────────────────────
const pendingDelete = ref<{ id: number; name: string } | null>(null);

async function confirmDelete() {
  if (!pendingDelete.value) return;
  await deleteNotificationChannel(pendingDelete.value.id);
  store.channels = store.channels.filter((c) => c.id !== pendingDelete.value!.id);
  pendingDelete.value = null;
}

// ── helpers ───────────────────────────────────────────────────────────────────
const PROVIDER_LABELS: Record<string, string> = {
  ntfy: "ntfy",
  gotify: "Gotify",
  discord: "Discord",
  telegram: "Telegram",
  apprise: "Apprise URL",
  webhook: "Webhook",
};

const NTFY_PRIORITIES = ["min", "low", "default", "high", "urgent"];
</script>

<template>
  <main class="page">
    <div class="page-header">
      <h1><span class="mdi mdi-bell-outline"></span> Notifications</h1>
      <button class="btn-primary" @click="openAdd">
        <span class="mdi mdi-plus"></span> Add Channel
      </button>
    </div>

    <!-- Channel list -->
    <div class="card">
      <table v-if="store.channels.length" class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Provider</th>
            <th>On Failure</th>
            <th>On Success</th>
            <th>Enabled</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ch in store.channels" :key="ch.id">
            <td>{{ ch.name }}</td>
            <td><span class="provider-badge">{{ PROVIDER_LABELS[ch.provider] ?? ch.provider }}</span></td>
            <td>
              <span class="mdi" :class="ch.notify_on_failure ? 'mdi-check-circle text-success' : 'mdi-minus-circle text-muted'"></span>
            </td>
            <td>
              <span class="mdi" :class="ch.notify_on_success ? 'mdi-check-circle text-success' : 'mdi-minus-circle text-muted'"></span>
            </td>
            <td>
              <span class="mdi" :class="ch.enabled ? 'mdi-toggle-switch text-success' : 'mdi-toggle-switch-off text-muted'"></span>
            </td>
            <td class="actions">
              <!-- Test button -->
              <button
                class="btn-icon"
                :title="testState[ch.id] === 'error' ? (testError[ch.id] || 'Error') : 'Send test notification'"
                @click="runTest(ch.id)"
                :disabled="testState[ch.id] === 'loading'"
              >
                <span class="mdi"
                  :class="{
                    'mdi-send-outline': !testState[ch.id] || testState[ch.id] === 'idle',
                    'mdi-loading mdi-spin': testState[ch.id] === 'loading',
                    'mdi-check-circle text-success': testState[ch.id] === 'ok',
                    'mdi-alert-circle text-danger': testState[ch.id] === 'error',
                  }"
                ></span>
              </button>
              <button class="btn-icon" title="Edit" @click="openEdit(ch)">
                <span class="mdi mdi-pencil-outline"></span>
              </button>
              <button class="btn-icon danger" title="Delete" @click="pendingDelete = { id: ch.id, name: ch.name }">
                <span class="mdi mdi-delete-outline"></span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <span class="mdi mdi-bell-off-outline"></span>
        <p>No notification channels configured.</p>
        <button class="btn-primary" @click="openAdd">Add your first channel</button>
      </div>
    </div>

    <!-- Add / Edit form -->
    <div v-if="showForm" class="card form-card">
      <h2>{{ editingId !== null ? "Edit Channel" : "Add Channel" }}</h2>
      <form @submit.prevent="submitForm" class="notif-form">
        <div class="form-row">
          <div class="form-group">
            <label>Name</label>
            <input v-model="form.name" required placeholder="My ntfy channel" />
          </div>
          <div class="form-group">
            <label>Provider</label>
            <select v-model="form.provider">
              <option value="ntfy">ntfy</option>
              <option value="gotify">Gotify</option>
              <option value="discord">Discord</option>
              <option value="telegram">Telegram</option>
              <option value="apprise">Apprise URL</option>
              <option value="webhook">Generic webhook</option>
            </select>
          </div>
        </div>

        <!-- ntfy config -->
        <template v-if="form.provider === 'ntfy'">
          <div class="form-row">
            <div class="form-group">
              <label>Server URL</label>
              <input v-model="form.ntfy_url" placeholder="https://ntfy.sh" required />
            </div>
            <div class="form-group">
              <label>Topic</label>
              <input v-model="form.ntfy_topic" placeholder="my-rsync-alerts" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Priority</label>
              <select v-model="form.ntfy_priority">
                <option v-for="p in NTFY_PRIORITIES" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Access token <span class="hint-inline">(optional, for auth-protected server)</span></label>
              <input v-model="form.ntfy_token" placeholder="tk_..." type="password" autocomplete="off" />
            </div>
          </div>
        </template>

        <!-- gotify config -->
        <template v-else-if="form.provider === 'gotify'">
          <div class="form-row">
            <div class="form-group">
              <label>Server URL</label>
              <input v-model="form.gotify_url" placeholder="https://gotify.example.com" required />
            </div>
            <div class="form-group">
              <label>Application token</label>
              <input v-model="form.gotify_token" placeholder="App token" type="password" autocomplete="off" required />
            </div>
          </div>
          <div class="form-row half">
            <div class="form-group">
              <label>Priority <span class="hint-inline">(0–10)</span></label>
              <input v-model.number="form.gotify_priority" type="number" min="0" max="10" />
            </div>
          </div>
        </template>

        <!-- discord config -->
        <template v-else-if="form.provider === 'discord'">
          <div class="form-group">
            <label>Webhook URL</label>
            <input v-model="form.discord_webhook_url" placeholder="https://discord.com/api/webhooks/…" required />
          </div>
        </template>

        <!-- telegram config -->
        <template v-else-if="form.provider === 'telegram'">
          <div class="form-row">
            <div class="form-group">
              <label>Bot token</label>
              <input v-model="form.tg_bot_token" placeholder="123456:ABC-DEF…" type="password" autocomplete="off" required />
            </div>
            <div class="form-group">
              <label>Chat ID</label>
              <input v-model="form.tg_chat_id" placeholder="-1001234567890" required />
            </div>
          </div>
        </template>

        <!-- apprise raw URL -->
        <template v-else-if="form.provider === 'apprise'">
          <div class="form-group">
            <label>Apprise URL</label>
            <input v-model="form.apprise_url" placeholder="slack://TokenA/TokenB/TokenC/#channel" required />
            <div class="hint">Any Apprise-compatible URL — supports 137+ services.</div>
          </div>
        </template>

        <!-- generic webhook -->
        <template v-else-if="form.provider === 'webhook'">
          <div class="form-group">
            <label>URL</label>
            <input v-model="form.wh_url" placeholder="https://homeassistant.local/api/webhook/xyz" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Headers <span class="hint-inline">(JSON object)</span></label>
              <textarea v-model="form.wh_headers" rows="3" placeholder='{"Authorization": "Bearer token"}'></textarea>
            </div>
            <div class="form-group">
              <label>Body template <span class="hint-inline" v-pre>(optional, use {{title}} / {{message}})</span></label>
              <textarea v-model="form.wh_body_template" rows="3" placeholder='{"text": "{{title}}: {{message}}"}'></textarea>
              <div class="hint">Leave blank to send <code v-pre>{"title": "…", "message": "…"}</code>.</div>
            </div>
          </div>
        </template>

        <!-- trigger conditions -->
        <div class="form-row checkboxes">
          <label><input type="checkbox" v-model="form.notify_on_failure" /> Notify on failure</label>
          <label><input type="checkbox" v-model="form.notify_on_success" /> Notify on success</label>
          <label><input type="checkbox" v-model="form.enabled" /> Enabled</label>
        </div>

        <div v-if="saveError" class="error-msg">{{ saveError }}</div>

        <div class="form-actions">
          <button type="submit" class="btn-primary">
            <span class="mdi mdi-content-save"></span> Save
          </button>
          <button type="button" class="btn-secondary" @click="cancelForm">Cancel</button>
        </div>
      </form>
    </div>

    <!-- Delete confirm modal -->
    <ConfirmModal
      v-if="pendingDelete"
      title="Delete Channel"
      :message="`Delete channel '${pendingDelete.name}'?`"
      confirm-label="Delete"
      @confirm="confirmDelete"
      @cancel="pendingDelete = null"
    />
  </main>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header h1 {
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.form-card h2 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  text-align: left;
  padding: 8px 10px;
  color: var(--text-muted);
  font-weight: 600;
  border-bottom: 1px solid var(--border);
}

.data-table td {
  padding: 10px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.data-table tr:last-child td { border-bottom: none; }

.provider-badge {
  background: var(--tag-bg, rgba(99,102,241,0.15));
  color: var(--tag-text, #818cf8);
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 11px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px;
  border-radius: 4px;
  font-size: 16px;
  transition: color 0.12s, background 0.12s;
}

.btn-icon:hover { background: var(--row-hover); color: var(--text); }
.btn-icon.danger:hover { color: var(--danger); }
.btn-icon:disabled { opacity: 0.5; cursor: default; }

.text-success { color: var(--badge-success-text); }
.text-muted   { color: var(--text-muted); }
.text-danger  { color: var(--danger-btn); }

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.empty-state .mdi { font-size: 40px; display: block; margin-bottom: 10px; }
.empty-state p { margin-bottom: 16px; }

/* form */
.notif-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-row.half { grid-template-columns: 1fr; max-width: 240px; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-group input,
.form-group select,
.form-group textarea {
  background: var(--surface-alt);
  border: 1px solid var(--border-input);
  border-radius: 5px;
  color: var(--text);
  padding: 7px 10px;
  font-size: 13px;
  font-family: inherit;
}

.form-group textarea { resize: vertical; }

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--primary);
}

.hint { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.hint-inline { font-size: 11px; color: var(--text-muted); font-weight: 400; text-transform: none; }

.checkboxes {
  grid-template-columns: repeat(3, auto);
  justify-content: start;
  gap: 20px;
}

.checkboxes label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0;
  color: var(--text);
  cursor: pointer;
}

.error-msg {
  color: var(--danger-btn);
  font-size: 13px;
  background: rgba(239,68,68,0.08);
  border-radius: 5px;
  padding: 8px 12px;
}

.form-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.12s;
}

.btn-primary:hover { opacity: 0.88; }

.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary:hover { background: var(--row-hover); }

@media (max-width: 600px) {
  .form-row { grid-template-columns: 1fr; }
  .checkboxes { grid-template-columns: 1fr; gap: 10px; }
}
</style>
