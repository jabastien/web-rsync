<script setup lang="ts">
import { reactive, ref } from "vue";
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

.flag-group {
  margin-bottom: 14px;
}
.flag-group:last-child {
  margin-bottom: 0;
}

.flag-group-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6b7280;
  margin-bottom: 6px;
}

.flag-grid {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

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
.flag-chip:hover {
  background: #eff6ff;
  border-color: #93c5fd;
}

.flag-chip code {
  font-family: "Fira Code", "Cascadia Code", monospace;
  font-size: 12px;
  color: #1d4ed8;
  white-space: nowrap;
  min-width: 160px;
}

.flag-desc {
  font-size: 12px;
  color: #6b7280;
}
</style>
