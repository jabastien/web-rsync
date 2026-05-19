<script setup lang="ts">
import { reactive, ref, nextTick, onUnmounted } from "vue";
import cronstrue from "cronstrue";
import { previewTask } from "../api/client";

interface FormData {
  name: string;
  source_path: string;
  dest_path: string;
  rsync_options: string;
  exclude_patterns: string;
  include_patterns: string;
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
  exclude_patterns: props.initial?.exclude_patterns ?? "",
  include_patterns: props.initial?.include_patterns ?? "",
  schedule: props.initial?.schedule ?? "",
  enabled: props.initial?.enabled ?? true,
});

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
  if (!form.source_path || !form.dest_path) return;
  clearPreview();
  previewRunning.value = true;

  try {
    const res = await previewTask({
      source_path: form.source_path,
      dest_path: form.dest_path,
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
      <div class="hint">
        Raw flags passed to rsync.
        <button type="button" class="flag-toggle" @click="showFlags = !showFlags">
          {{ showFlags ? "Hide" : "Browse" }} flags ▾
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
        <span class="preview-title">Dry-Run Test</span>
        <button
          type="button"
          class="btn-preview"
          :disabled="previewRunning || !form.source_path || !form.dest_path"
          @click="runPreview"
        >
          <span v-if="previewRunning" class="spinner" />
          {{ previewRunning ? "Running…" : "▶ Test Dry Run" }}
        </button>
        <button
          v-if="previewDone"
          type="button"
          class="btn-clear"
          @click="clearPreview"
        >✕ Clear</button>
        <span
          v-if="previewDone"
          class="preview-badge"
          :class="previewStatus === 'success' ? 'badge-ok' : 'badge-err'"
        >
          {{ previewStatus === "success" ? "✓ OK" : "✗ Failed" }}
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

<style scoped>
/* ── Flag reference ── */
.flag-toggle {
  background: none;
  border: none;
  color: #2563eb;
  font-size: 11px;
  padding: 0;
  margin-left: 8px;
  cursor: pointer;
  text-decoration: underline;
}

.flag-reference {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: #f9fafb;
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
  color: #6b7280;
  margin-bottom: 6px;
}

.flag-grid { display: flex; flex-direction: column; gap: 3px; }

.flag-chip {
  display: flex;
  align-items: baseline;
  gap: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 5px 10px;
  text-align: left;
  cursor: pointer;
  transition: background 0.1s, border-color 0.1s;
  width: 100%;
}
.flag-chip:hover { background: #eff6ff; border-color: #93c5fd; }
.flag-chip code {
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  color: #1d4ed8;
  white-space: nowrap;
  min-width: 160px;
}
.flag-desc { font-size: 12px; color: #6b7280; }

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
  color: #9ca3af;
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
}

/* ── Dry-run preview ── */
.preview-section {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 14px;
  background: #f9fafb;
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.preview-title {
  font-weight: 600;
  font-size: 13px;
  color: #374151;
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

.btn-clear {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}
.btn-clear:hover { color: #374151; }

.preview-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 9999px;
}
.badge-ok  { background: #dcfce7; color: #166534; }
.badge-err { background: #fee2e2; color: #991b1b; }

.preview-hint {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 10px;
}
.preview-hint code {
  font-family: monospace;
  background: #e5e7eb;
  padding: 1px 4px;
  border-radius: 3px;
}

.preview-log {
  background: #0f172a;
  color: #94a3b8;
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
.log-waiting { color: #475569; font-style: italic; }

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
</style>
