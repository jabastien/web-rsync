<script setup lang="ts">
import cronstrue from "cronstrue";

defineProps<{ schedule: string | null }>();

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
    <span class="mdi mdi-calendar-clock"></span>{{ schedule }}
  </span>
  <span v-else class="badge badge-manual">
    <span class="mdi mdi-hand-pointing-right"></span>manual
  </span>
</template>

<style scoped>
.badge-manual {
  background: var(--badge-manual-bg);
  color: var(--badge-manual-text);
}
.badge .mdi {
  font-size: 11px;
  margin-right: 2px;
}
</style>
