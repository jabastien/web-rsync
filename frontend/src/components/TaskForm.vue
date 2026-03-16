<script setup lang="ts">
import { reactive, watch } from "vue";
import cronstrue from "cronstrue";

interface FormData {
  name: string;
  source_path: string;
  dest_path: string;
  rsync_options: string;
  schedule: string;
  enabled: boolean;
}

const props = defineProps<{ initial?: Partial<FormData> }>();
const emit = defineEmits<{ submit: [data: FormData] }>();

const form = reactive<FormData>({
  name: props.initial?.name ?? "",
  source_path: props.initial?.source_path ?? "",
  dest_path: props.initial?.dest_path ?? "",
  rsync_options: props.initial?.rsync_options ?? "-avz",
  schedule: props.initial?.schedule ?? "",
  enabled: props.initial?.enabled ?? true,
});

function cronHint(cron: string): string {
  if (!cron) return "";
  try {
    return cronstrue.toString(cron, { use24HourTimeFormat: true });
  } catch {
    return "Invalid cron expression";
  }
}

function submit() {
  emit("submit", { ...form, schedule: form.schedule || null } as any);
}
</script>

<template>
  <form @submit.prevent="submit">
    <div class="form-group">
      <label>Name</label>
      <input v-model="form.name" required />
    </div>
    <div class="form-group">
      <label>Source Path</label>
      <input v-model="form.source_path" placeholder="/path/to/source/" required />
    </div>
    <div class="form-group">
      <label>Destination Path</label>
      <input v-model="form.dest_path" placeholder="user@host:/path/to/dest/" required />
    </div>
    <div class="form-group">
      <label>rsync Options</label>
      <input v-model="form.rsync_options" placeholder="-avz --delete" />
      <div class="hint">Raw flags passed to rsync</div>
    </div>
    <div class="form-group">
      <label>Schedule (cron)</label>
      <input v-model="form.schedule" placeholder="0 2 * * * — leave blank for manual" />
      <div class="hint" v-if="form.schedule">{{ cronHint(form.schedule) }}</div>
    </div>
    <div class="form-group">
      <label>
        <input type="checkbox" v-model="form.enabled" />
        Enabled
      </label>
    </div>
    <button type="submit" class="btn-primary">Save</button>
  </form>
</template>
