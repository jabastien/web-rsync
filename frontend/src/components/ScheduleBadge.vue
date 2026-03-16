<script setup lang="ts">
import cronstrue from "cronstrue";

const props = defineProps<{ schedule: string | null }>();

function humanize(cron: string): string {
  try {
    return cronstrue.toString(cron, { use24HourTimeFormat: true });
  } catch {
    return cron;
  }
}
</script>

<template>
  <span v-if="schedule" class="badge badge-scheduled" :title="humanize(schedule)">
    {{ schedule }}
  </span>
  <span v-else class="badge" style="background:#f3f4f6;color:#6b7280">manual</span>
</template>
