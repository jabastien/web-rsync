<script setup lang="ts">
import { reactive, ref, computed, onMounted, nextTick, onUnmounted } from "vue";
import cronstrue from "cronstrue";
import { previewTask, getMounts } from "../api/client";
import { useHostsStore } from "../stores/hosts";
import type { Host } from "../stores/hosts";

interface MountEntry {
  mountpoint: string;
  device: string;
  fstype: string;
  access: "rw" | "ro";
}

interface FormData {
  name: string;
  rsync_options: string;
  exclude_patterns: string;
  include_patterns: string;
  schedule: string;
  enabled: boolean;
  notify_enabled: boolean;
}

const props = defineProps<{
  initial?: Partial<FormData & { source_path: string; dest_path: string }>;
}>();
const emit = defineEmits<{ submit: [data: FormData & { source_path: string; dest_path: string }] }>();

const form = reactive<FormData>({
  name: props.initial?.name ?? "",
  rsync_options: props.initial?.rsync_options ?? "-avz",
  exclude_patterns: props.initial?.exclude_patterns ?? "",
  include_patterns: props.initial?.include_patterns ?? "",
  schedule: props.initial?.schedule ?? "",
  enabled: props.initial?.enabled ?? true,
  notify_enabled: props.initial?.notify_enabled ?? true,
});

// ── Hosts + endpoint pickers ──────────────────────────────────────────────────
const hostsStore = useHostsStore();
const sourceHostId = ref<number | null>(null);
const sourcePath = ref("");
const destHostId = ref<number | null>(null);
const destPath = ref("");

function buildPath(hostId: number | null, path: string): string {
  if (hostId === null) return path;
  const h = hostsStore.hosts.find((h: Host) => h.id === hostId);
  if (!h) return path;
  return `${h.username}@${h.hostname}:${path}`;
}

function decomposePath(full: string): { hostId: number | null; path: string } {
  for (const h of hostsStore.hosts) {
    const prefix = `${h.username}@${h.hostname}:`;
    if (full.startsWith(prefix)) return { hostId: h.id, path: full.slice(prefix.length) };
  }
  return { hostId: null, path: full };
}

onMounted(async () => {
  await hostsStore.fetchAll();
  if (props.initial?.source_path) {
    const d = decomposePath(props.initial.source_path);
    sourceHostId.value = d.hostId;
    sourcePath.value = d.path;
  }
  if (props.initial?.dest_path) {
    const d = decomposePath(props.initial.dest_path);
    destHostId.value = d.hostId;
    destPath.value = d.path;
  }
});

const computedSourcePath = computed(() => buildPath(sourceHostId.value, sourcePath.value));
const computedDestPath   = computed(() => buildPath(destHostId.value, destPath.value));

// ── Flag reference panel ──────────────────────────────────────────────────────
const showFlags = ref(false);

const FLAG_GROUPS: { group: string; flags: { flag: string; desc: string }[] }[] = [
  {
    group: "Common",
    flags: [
      { flag: "-v", desc: "Verbose output" },
      { flag: "-a", desc: "Archive mode (equals -rlptgoD)" },
      { flag: "-z", desc: "Compress during transfer" },
      { flag: "-r", desc: "Recurse into directories" },
      { flag: "-u", desc: "Skip files newer on receiver" },
      { flag: "-n", desc: "Dry run (no changes made)" },
      { flag: "-q", desc: "Quiet — suppress non-error output" },
      { flag: "-P", desc: "Show progress + keep partial files" },
      { flag: "--progress", desc: "Show file transfer progress" },
      { flag: "--stats", desc: "Print transfer statistics" },
    ],
  },
  {
    group: "Sync Behaviour",
    flags: [
      { flag: "--delete", desc: "Delete files not in source" },
      { flag: "--delete-before", desc: "Delete before transfer" },
      { flag: "--delete-after", desc: "Delete after transfer" },
      { flag: "--delete-excluded", desc: "Also delete excluded files from dest" },
      { flag: "--ignore-existing", desc: "Skip files that already exist on receiver" },
      { flag: "--remove-source-files", desc: "Remove source files after transfer" },
      { flag: "--update", desc: "Skip files newer on receiver (alias -u)" },
      { flag: "--inplace", desc: "Update destination files in-place" },
      { flag: "--append", desc: "Append data to shorter files" },
      { flag: "--backup", desc: "Make backups of changed files" },
      { flag: "--backup-dir=DIR", desc: "Store backups in this directory" },
      { flag: "--suffix=SUFFIX", desc: "Backup file suffix (default ~)" },
    ],
  },
  {
    group: "File Selection",
    flags: [
      { flag: "--exclude=PATTERN", desc: "Exclude files matching pattern" },
      { flag: "--exclude-from=FILE", desc: "Read exclude patterns from file" },
      { flag: "--include=PATTERN", desc: "Include files matching pattern" },
      { flag: "--include-from=FILE", desc: "Read include patterns from file" },
      { flag: "--filter=RULE", desc: "Add a file-filtering rule" },
      { flag: "--max-size=SIZE", desc: "Skip files larger than SIZE" },
      { flag: "--min-size=SIZE", desc: "Skip files smaller than SIZE" },
      { flag: "--max-age=DAYS", desc: "Skip files older than DAYS" },
      { flag: "--min-age=DAYS", desc: "Skip files newer than DAYS" },
    ],
  },
  {
    group: "Permissions & Ownership",
    flags: [
      { flag: "-p", desc: "Preserve permissions" },
      { flag: "-o", desc: "Preserve owner" },
      { flag: "-g", desc: "Preserve group" },
      { flag: "-t", desc: "Preserve modification times" },
      { flag: "-A", desc: "Preserve ACLs" },
      { flag: "-X", desc: "Preserve extended attributes" },
      { flag: "--chmod=CHMOD", desc: "Set dest permissions (e.g. a+r)" },
      { flag: "--chown=USER:GROUP", desc: "Set dest owner/group" },
    ],
  },
  {
    group: "Links & Special Files",
    flags: [
      { flag: "-l", desc: "Preserve symlinks" },
      { flag: "-L", desc: "Transform symlinks into referents" },
      { flag: "-H", desc: "Preserve hard links" },
      { flag: "-D", desc: "Preserve device and special files" },
      { flag: "--safe-links", desc: "Ignore symlinks outside source tree" },
      { flag: "--copy-links", desc: "Copy the referent of symlinks" },
      { flag: "--copy-dirlinks", desc: "Copy referents of symlinked dirs" },
    ],
  },
  {
    group: "SSH / Network",
    flags: [
      { flag: "-e CMD", desc: "Specify remote shell (e.g. ssh -p 2222)" },
      { flag: "--bwlimit=KBPS", desc: "Limit bandwidth in KB/s" },
      { flag: "--port=PORT", desc: "rsync daemon port" },
      { flag: "--timeout=SEC", desc: "I/O timeout in seconds" },
      { flag: "--contimeout=SEC", desc: "Connect timeout in seconds" },
      { flag: "--blocking-io", desc: "Use blocking I/O for the remote shell" },
      { flag: "--compress-level=NUM", desc: "Compression level (1-9)" },
    ],
  },
  {
    group: "Checksums & Integrity",
    flags: [
      { flag: "-c", desc: "Skip based on checksum, not mod-time/size" },
      { flag: "--checksum", desc: "Same as -c" },
      { flag: "--ignore-times", desc: "Always transfer, even if up to date" },
      { flag: "--size-only", desc: "Skip if size matches (ignore time)" },
    ],
  },
  {
    group: "Output & Logging",
    flags: [
      { flag: "--log-file=FILE", desc: "Log to file instead of stderr" },
      { flag: "--log-format=FMT", desc: "Log format string" },
      { flag: "--itemize-changes", desc: "Output a change summary for every item" },
      { flag: "--human-readable", desc: "Output in human-readable format" },
      { flag: "--list-only", desc: "List source files only, no transfer" },
    ],
  },
];

function appendFlag(flag: string) {
  const current = form.rsync_options.trim();
  if (!current.includes(flag)) {
    form.rsync_options = current ? `${current} ${flag}` : flag;
  }
}

// ── Dry-run preview ───────────────────────────────────────────────────────────
const previewRunId = ref<number | null>(null);
const previewRunning = ref(false);
const previewDone = ref(false);
const previewStatus = ref<"success" | "failed" | null>(null);
const previewLines = ref<string[]>([]);
const logContainer = ref<HTMLElement | null>(null);
let previewEs: EventSource | null = null;

function clearPreview() {
  previewEs?.close();
  previewEs = null;
  previewRunId.value = null;
  previewRunning.value = false;
  previewDone.value = false;
  previewStatus.value = null;
  previewLines.value = [];
}

async function runPreview() {
  if (!computedSourcePath.value || !computedDestPath.value) return;
  clearPreview();
  previewRunning.value = true;

  try {
    const res = await previewTask({
      source_path: computedSourcePath.value,
      dest_path: computedDestPath.value,
      rsync_options: form.rsync_options,
      exclude_patterns: form.exclude_patterns,
      include_patterns: form.include_patterns,
    });
    previewRunId.value = res.data.run_id;
    streamPreview(res.data.run_id);
  } catch (e: any) {
    previewLines.value = [`[ERROR] ${e.response?.data?.detail ?? e.message}`];
    previewRunning.value = false;
    previewDone.value = true;
    previewStatus.value = "failed";
  }
}

function streamPreview(runId: number) {
  previewEs = new EventSource(`/api/job-runs/${runId}/stream`);

  previewEs.onmessage = (e) => {
    previewLines.value.push(e.data);
    nextTick(() => {
      if (logContainer.value)
        logContainer.value.scrollTop = logContainer.value.scrollHeight;
    });
  };

  previewEs.addEventListener("done", (e: any) => {
    previewStatus.value = e.data === "success" ? "success" : "failed";
    previewLines.value.push(`\n─── ${previewStatus.value.toUpperCase()} ───`);
    previewRunning.value = false;
    previewDone.value = true;
    previewEs?.close();
    nextTick(() => {
      if (logContainer.value)
        logContainer.value.scrollTop = logContainer.value.scrollHeight;
    });
  });

  previewEs.onerror = () => {
    previewRunning.value = false;
    previewDone.value = true;
    previewEs?.close();
  };
}

onUnmounted(() => previewEs?.close());

// ── Mount points panel ────────────────────────────────────────────────────────
const showMounts = ref(false);
const mountsLoading = ref(false);
const mountsLoaded = ref(false);
const mountsList = ref<MountEntry[]>([]);
const copiedMount = ref<string | null>(null);

async function toggleMounts() {
  showMounts.value = !showMounts.value;
  if (showMounts.value && !mountsLoaded.value) {
    mountsLoading.value = true;
    try {
      const res = await getMounts();
      mountsList.value = res.data;
      mountsLoaded.value = true;
    } catch {
      mountsList.value = [];
    } finally {
      mountsLoading.value = false;
    }
  }
}

async function copyMount(path: string) {
  try {
    await navigator.clipboard.writeText(path);
    copiedMount.value = path;
    setTimeout(() => { copiedMount.value = null; }, 1500);
  } catch { /* clipboard unavailable */ }
}

// ── Cron hint ─────────────────────────────────────────────────────────────────
function cronHint(cron: string): string {
  if (!cron) return "";
  try {
    return cronstrue.toString(cron, { use24HourTimeFormat: true });
  } catch {
    return "Invalid cron expression";
  }
}

function submit() {
  emit("submit", {
    ...form,
    source_path: computedSourcePath.value,
    dest_path: computedDestPath.value,
    schedule: form.schedule || null,
  } as any);
}
</script>

<template>
  <form @submit.prevent="submit">
    <div class="form-group">
      <label>Name</label>
      <input v-model="form.name" required />
    </div>

    <!-- ── Source ── -->
    <div class="form-group">
      <label>Source</label>
      <div class="endpoint-row">
        <select v-model="sourceHostId" class="host-select">
          <option :value="null">
            <span class="mdi mdi-server-outline"></span>Local — this server
          </option>
          <option v-for="h in hostsStore.hosts" :key="h.id" :value="h.id">
            {{ h.name }} — {{ h.username }}@{{ h.hostname }}
          </option>
        </select>
        <input
          v-model="sourcePath"
          class="path-input"
          placeholder="/path/to/source/"
          required
        />
      </div>
      <div class="hint" v-if="sourceHostId !== null && sourcePath">
        <span class="mdi mdi-arrow-right-thin"></span>
        <code>{{ computedSourcePath }}</code>
      </div>
    </div>

    <!-- ── Destination ── -->
    <div class="form-group">
      <label>Destination</label>
      <div class="endpoint-row">
        <select v-model="destHostId" class="host-select">
          <option :value="null">Local — this server</option>
          <option v-for="h in hostsStore.hosts" :key="h.id" :value="h.id">
            {{ h.name }} — {{ h.username }}@{{ h.hostname }}
          </option>
        </select>
        <input
          v-model="destPath"
          class="path-input"
          placeholder="/path/to/dest/"
          required
        />
      </div>
      <div class="hint" v-if="destHostId !== null && destPath">
        <span class="mdi mdi-arrow-right-thin"></span>
        <code>{{ computedDestPath }}</code>
      </div>
    </div>

    <!-- ── Mount points panel ── -->
    <div class="mounts-panel">
      <button type="button" class="mounts-toggle" @click="toggleMounts">
        <span class="mdi" :class="showMounts ? 'mdi-chevron-down' : 'mdi-chevron-right'"></span>
        <span class="mdi mdi-harddisk" style="margin-right:4px"></span>
        Available local paths
        <span class="mdi mdi-loading mdi-spin" v-if="mountsLoading" style="margin-left:6px;font-size:14px"></span>
      </button>
      <div v-if="showMounts && !mountsLoading" class="mounts-list">
        <div v-if="mountsList.length === 0" class="mounts-empty">No mount points found.</div>
        <div
          v-for="m in mountsList"
          :key="m.mountpoint"
          class="mount-row"
          @click="copyMount(m.mountpoint)"
          :title="`Click to copy: ${m.mountpoint}`"
        >
          <span class="mdi mdi-folder-outline mount-icon"></span>
          <code class="mount-path">{{ m.mountpoint }}</code>
          <span class="mount-badge" :class="m.access === 'rw' ? 'badge-rw' : 'badge-ro'">{{ m.access }}</span>
          <span class="mount-fstype">{{ m.fstype }}</span>
          <span class="mdi mount-copy-hint" :class="copiedMount === m.mountpoint ? 'mdi-check mount-copied' : 'mdi-content-copy'"></span>
        </div>
      </div>
    </div>

    <div class="form-group">
      <label>rsync Options</label>
      <input v-model="form.rsync_options" placeholder="-avz --delete" />
      <div class="hint">
        Raw flags passed to rsync.
        <button type="button" class="flag-toggle" @click="showFlags = !showFlags">
          <span class="mdi" :class="showFlags ? 'mdi-chevron-up' : 'mdi-chevron-down'"></span>
          {{ showFlags ? "Hide" : "Browse" }} flags
        </button>
      </div>
    </div>

    <div v-if="showFlags" class="flag-reference">
      <div v-for="group in FLAG_GROUPS" :key="group.group" class="flag-group">
        <div class="flag-group-title">{{ group.group }}</div>
        <div class="flag-grid">
          <button
            v-for="f in group.flags"
            :key="f.flag"
            type="button"
            class="flag-chip"
            :title="f.desc"
            @click="appendFlag(f.flag)"
          >
            <span class="mdi mdi-plus-circle-outline flag-add-icon"></span>
            <code>{{ f.flag }}</code>
            <span class="flag-desc">{{ f.desc }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Pattern filters -->
    <div class="patterns-row">
      <div class="form-group" style="flex:1">
        <label>Include Patterns <span class="label-hint">(--include-from)</span></label>
        <textarea
          v-model="form.include_patterns"
          class="pattern-textarea"
          placeholder="One pattern per line&#10;e.g. *.conf&#10;     important/"
          spellcheck="false"
        />
        <div class="hint">Files matching these patterns are always included, even if an exclude pattern would otherwise skip them. Applied before excludes.</div>
      </div>
      <div class="form-group" style="flex:1">
        <label>Exclude Patterns <span class="label-hint">(--exclude-from)</span></label>
        <textarea
          v-model="form.exclude_patterns"
          class="pattern-textarea"
          placeholder="One pattern per line&#10;e.g. *.tmp&#10;     .cache/&#10;     node_modules/"
          spellcheck="false"
        />
        <div class="hint">Files matching these patterns are skipped. Use <code>/</code> suffix for directories, <code>*</code> as wildcard.</div>
      </div>
    </div>

    <!-- Dry-run preview -->
    <div class="preview-section">
      <div class="preview-header">
        <span class="mdi mdi-play-circle-outline preview-icon"></span>
        <span class="preview-title">Dry-Run Test</span>
        <button
          type="button"
          class="btn-preview"
          :disabled="previewRunning || !sourcePath || !destPath"
          @click="runPreview"
        >
          <span v-if="previewRunning" class="spinner" />
          <span v-else class="mdi mdi-play"></span>
          {{ previewRunning ? "Running…" : "Test Dry Run" }}
        </button>
        <button
          v-if="previewDone"
          type="button"
          class="btn-clear"
          @click="clearPreview"
        >
          <span class="mdi mdi-close"></span>
        </button>
        <span
          v-if="previewDone"
          class="preview-badge"
          :class="previewStatus === 'success' ? 'badge-ok' : 'badge-err'"
        >
          <span class="mdi" :class="previewStatus === 'success' ? 'mdi-check' : 'mdi-close'"></span>
          {{ previewStatus === "success" ? "OK" : "Failed" }}
        </span>
      </div>
      <div class="preview-hint">
        Runs rsync <code>--dry-run</code> with the current paths and options — no files will be transferred.
      </div>

      <div
        v-if="previewRunning || previewLines.length"
        class="preview-log"
        ref="logContainer"
      >
        <pre v-if="previewLines.length === 0" class="log-waiting">Waiting for output…</pre>
        <pre v-for="(line, i) in previewLines" :key="i">{{ line }}</pre>
      </div>
    </div>

    <div class="form-group">
      <label>Schedule (cron)</label>
      <input v-model="form.schedule" placeholder="0 2 * * * — leave blank for manual" />
      <div class="hint">
        5-field cron syntax. Leave blank for manual-only.
        <a href="https://crontab.guru/" target="_blank" rel="noopener">crontab.guru</a> ↗
      </div>
      <div class="hint" v-if="form.schedule">{{ cronHint(form.schedule) }}</div>
    </div>
    <div class="form-group">
      <label>
        <input type="checkbox" v-model="form.enabled" />
        Enabled
      </label>
    </div>
    <div class="form-group">
      <label>
        <input type="checkbox" v-model="form.notify_enabled" />
        Enable notifications for this task
      </label>
      <div class="hint">When checked, configured notification channels fire on job completion.</div>
    </div>
    <button type="submit" class="btn-primary">
      <span class="mdi mdi-content-save"></span>Save
    </button>
  </form>
</template>

<style scoped>
/* ── Endpoint picker ── */
.endpoint-row {
  display: flex;
  gap: 8px;
}

.host-select {
  width: 220px;
  flex-shrink: 0;
  padding: 7px 10px;
  border: 1px solid var(--border-input);
  border-radius: 4px;
  font-size: 13px;
  background: var(--surface-alt);
  color: var(--text);
  cursor: pointer;
}
.host-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(96,165,250,.15);
}

.path-input {
  flex: 1;
  min-width: 0;
  padding: 7px 10px;
  border: 1px solid var(--border-input);
  border-radius: 4px;
  font-size: 13px;
  background: var(--surface-alt);
  color: var(--text);
  font-family: "Fira Code", "Cascadia Code", ui-monospace, monospace;
}
.path-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(96,165,250,.15);
}

@media (max-width: 600px) {
  .endpoint-row { flex-direction: column; }
  .host-select { width: 100%; }
}

/* ── Flag reference ── */
.flag-toggle {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 11px;
  padding: 0 4px;
  margin-left: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border-radius: 3px;
}
.flag-toggle:hover { text-decoration: underline; }
.flag-toggle .mdi { font-size: 13px; }

.flag-reference {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: var(--surface-alt);
  max-height: 420px;
  overflow-y: auto;
}

.flag-group { margin-bottom: 14px; }
.flag-group:last-child { margin-bottom: 0; }

.flag-group-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  margin-bottom: 6px;
}

.flag-grid { display: flex; flex-direction: column; gap: 3px; }

.flag-chip {
  display: flex;
  align-items: baseline;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 5px 10px;
  text-align: left;
  cursor: pointer;
  transition: background 0.1s, border-color 0.1s;
  width: 100%;
}
.flag-chip:hover { background: var(--row-selected); border-color: var(--primary); }
.flag-add-icon { font-size: 13px; color: var(--text-faint); align-self: center; }
.flag-chip:hover .flag-add-icon { color: var(--primary); }

.flag-chip code {
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  color: var(--text-code);
  white-space: nowrap;
  min-width: 160px;
  background: none;
  padding: 0;
}
.flag-desc { font-size: 12px; color: var(--text-muted); }

/* ── Pattern filters ── */
.patterns-row {
  display: flex;
  gap: 16px;
  margin-bottom: 0;
}
.patterns-row .form-group { margin-bottom: 14px; }

.label-hint {
  font-weight: 400;
  font-size: 11px;
  color: var(--text-faint);
  font-family: "Fira Code", "Cascadia Code", monospace;
}

.pattern-textarea {
  width: 100%;
  min-height: 90px;
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
  background: var(--surface-alt);
  color: var(--text);
  border: 1px solid var(--border-input);
  border-radius: 4px;
  padding: 7px 10px;
}
.pattern-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(96,165,250,.15);
}

/* ── Dry-run preview ── */
.preview-section {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: var(--surface-alt);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.preview-icon { font-size: 18px; color: var(--text-muted); }

.preview-title {
  font-weight: 600;
  font-size: 13px;
  color: var(--text);
}

.btn-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #0f766e;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 5px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.btn-preview:hover:not(:disabled) { background: #0d6460; }
.btn-preview:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-preview .mdi { font-size: 14px; }

.btn-clear {
  background: none;
  border: none;
  color: var(--text-faint);
  font-size: 14px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  display: flex;
  align-items: center;
}
.btn-clear:hover { color: var(--text); background: var(--border); }
.btn-clear .mdi { font-size: 16px; }

.preview-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.preview-badge .mdi { font-size: 12px; }
.badge-ok  { background: var(--badge-success-bg); color: var(--badge-success-text); }
.badge-err { background: var(--badge-failed-bg);  color: var(--badge-failed-text); }

.preview-hint {
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 10px;
}

.preview-log {
  background: var(--log-bg);
  color: var(--log-text);
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  line-height: 1.5;
  padding: 10px 14px;
  border-radius: 5px;
  max-height: 320px;
  overflow-y: auto;
}
.preview-log pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
.log-waiting { color: var(--text-faint); font-style: italic; }

/* ── Spinner ── */
.spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255,255,255,.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .patterns-row { flex-direction: column; }
}

/* ── Mount points panel ── */
.mounts-panel {
  margin-bottom: 14px;
}

.mounts-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background 0.1s, border-color 0.1s, color 0.1s;
}
.mounts-toggle:hover {
  background: var(--surface-alt);
  border-color: var(--primary);
  color: var(--text);
}
.mounts-toggle .mdi { font-size: 15px; }

.mounts-list {
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 5px 5px;
  overflow: hidden;
  max-height: 260px;
  overflow-y: auto;
}

.mounts-empty {
  padding: 10px 14px;
  font-size: 12px;
  color: var(--text-faint);
}

.mount-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  cursor: pointer;
  transition: background 0.1s;
  border-bottom: 1px solid var(--border);
}
.mount-row:last-child { border-bottom: none; }
.mount-row:hover { background: var(--row-hover); }

.mount-icon { font-size: 14px; color: var(--text-faint); flex-shrink: 0; }

.mount-path {
  flex: 1;
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  color: var(--text-code);
  background: none;
  padding: 0;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mount-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 9999px;
  flex-shrink: 0;
}
.badge-rw { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.badge-ro { background: rgba(148, 163, 184, 0.15); color: var(--text-faint); }

.mount-fstype {
  font-size: 11px;
  color: var(--text-faint);
  flex-shrink: 0;
  min-width: 40px;
}

.mount-copy-hint {
  font-size: 13px;
  color: var(--text-faint);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.1s, color 0.1s;
}
.mount-row:hover .mount-copy-hint { opacity: 1; }
.mount-copied { color: #4ade80 !important; opacity: 1 !important; }
</style>
