<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { getJobLog } from "../api/client";

const props = defineProps<{ runId: number; live?: boolean }>();

const lines = ref<string[]>([]);
const done = ref(false);
const container = ref<HTMLElement | null>(null);
let es: EventSource | null = null;

async function loadStatic() {
  const res = await getJobLog(props.runId);
  lines.value = res.data.log.split("\n");
  done.value = true;
}

function startStream() {
  es = new EventSource(`/api/job-runs/${props.runId}/stream`);
  es.onmessage = (e) => {
    lines.value.push(e.data);
    nextTick(() => {
      if (container.value) container.value.scrollTop = container.value.scrollHeight;
    });
  };
  es.addEventListener("done", (e: any) => {
    lines.value.push(`\n--- finished: ${e.data} ---`);
    done.value = true;
    es?.close();
  });
  es.onerror = () => {
    es?.close();
    done.value = true;
  };
}

onMounted(() => {
  if (props.live) {
    startStream();
  } else {
    loadStatic();
  }
});

onUnmounted(() => {
  es?.close();
});
</script>

<template>
  <div class="log-viewer" ref="container">
    <pre v-for="(line, i) in lines" :key="i">{{ line }}</pre>
    <p v-if="!done && lines.length === 0" class="log-waiting">Waiting for output…</p>
  </div>
</template>

<style scoped>
.log-viewer {
  background: #0f172a;
  color: #94a3b8;
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  line-height: 1.5;
  padding: 12px 16px;
  border-radius: 6px;
  height: 420px;
  overflow-y: auto;
}
.log-viewer pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
.log-waiting { color: #475569; font-style: italic; }
</style>
