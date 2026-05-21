<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { getJobLog } from "../api/client";

const props = defineProps<{ runId: number; live?: boolean }>();
const emit = defineEmits<{ done: [] }>();

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
    emit("done");
  });
  es.onerror = () => {
    es?.close();
    done.value = true;
    emit("done");
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

function downloadLog() {
  const content = lines.value.join("\n");
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `web-rsync-run-${props.runId}.log`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="log-wrapper">
    <div class="log-toolbar">
      <button
        class="download-btn"
        @click="downloadLog"
        :disabled="lines.length === 0"
        title="Download log"
      >
        <span class="mdi mdi-download"></span> Download
      </button>
    </div>
    <div class="log-viewer" ref="container">
      <pre v-for="(line, i) in lines" :key="i">{{ line }}</pre>
      <p v-if="!done && lines.length === 0" class="log-waiting">
        <span class="mdi mdi-loading mdi-spin"></span> Waiting for output…
      </p>
    </div>
  </div>
</template>

<style scoped>
.log-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.log-toolbar {
  display: flex;
  justify-content: flex-end;
}

.download-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--text-muted);
  border-radius: 4px;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.12s, border-color 0.12s;
}
.download-btn .mdi { font-size: 14px; }
.download-btn:hover:not(:disabled) {
  color: var(--primary);
  border-color: var(--primary);
}
.download-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.log-viewer {
  background: var(--log-bg);
  color: var(--log-text);
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
.log-waiting {
  color: var(--text-faint);
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 6px;
}
.log-waiting .mdi { font-size: 14px; }
</style>
