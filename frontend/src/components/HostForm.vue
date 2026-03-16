<script setup lang="ts">
import { reactive } from "vue";

interface FormData {
  name: string;
  hostname: string;
  port: number;
  username: string;
  ssh_key_path: string;
}

const props = defineProps<{ initial?: Partial<FormData> }>();
const emit = defineEmits<{ submit: [data: FormData] }>();

const form = reactive<FormData>({
  name: props.initial?.name ?? "",
  hostname: props.initial?.hostname ?? "",
  port: props.initial?.port ?? 22,
  username: props.initial?.username ?? "",
  ssh_key_path: props.initial?.ssh_key_path ?? "",
});

function submit() {
  emit("submit", { ...form, ssh_key_path: form.ssh_key_path || null } as any);
}
</script>

<template>
  <form @submit.prevent="submit">
    <div class="form-group">
      <label>Name</label>
      <input v-model="form.name" required />
    </div>
    <div class="form-group">
      <label>Hostname / IP</label>
      <input v-model="form.hostname" required />
    </div>
    <div class="form-group">
      <label>Port</label>
      <input v-model.number="form.port" type="number" min="1" max="65535" />
    </div>
    <div class="form-group">
      <label>Username</label>
      <input v-model="form.username" required />
    </div>
    <div class="form-group">
      <label>SSH Key Path (optional)</label>
      <input v-model="form.ssh_key_path" placeholder="/data/ssh/id_rsa" />
      <div class="hint">Leave blank to use the auto-generated key</div>
    </div>
    <button type="submit" class="btn-primary">Save</button>
  </form>
</template>
