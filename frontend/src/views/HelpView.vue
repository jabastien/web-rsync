<template>
  <div class="page">
    <h1 class="page-title">Help</h1>

    <div class="card section">
      <h2>What is web-RSync?</h2>
      <p>
        web-RSync is a browser-based manager for <strong>rsync</strong> jobs. It lets you define,
        schedule, and monitor file-synchronization tasks between local and remote machines — without
        touching the command line after the initial setup.
      </p>
      <p>Typical use cases:</p>
      <ul>
        <li>Automated nightly backups from a server to a NAS</li>
        <li>Keeping two remote machines in sync on a schedule</li>
        <li>One-shot manual transfers with real-time progress</li>
        <li>Validating rsync options with a dry-run before committing</li>
      </ul>
    </div>

    <div class="card section">
      <h2>Tasks</h2>
      <p>
        A <strong>Task</strong> defines one rsync job: source path, destination path, rsync options,
        and an optional cron schedule.
      </p>

      <h3>Path formats</h3>
      <table>
        <thead><tr><th>Scenario</th><th>Source example</th><th>Destination example</th></tr></thead>
        <tbody>
          <tr><td>Local → local</td><td><code>/home/user/docs/</code></td><td><code>/mnt/backup/</code></td></tr>
          <tr><td>Local → remote</td><td><code>/home/user/docs/</code></td><td><code>user@nas:/backup/</code></td></tr>
          <tr><td>Remote → local</td><td><code>user@nas:/data/</code></td><td><code>/mnt/local/</code></td></tr>
          <tr><td>Remote → remote</td><td><code>user@host1:/data/</code></td><td><code>user@host2:/backup/</code></td></tr>
        </tbody>
      </table>
      <p class="note">
        Trailing slash on the source matters: <code>src/</code> copies the <em>contents</em>;
        <code>src</code> copies the <em>directory itself</em>.
      </p>

      <h3>Remote → Remote</h3>
      <p>
        rsync does not natively support two remote endpoints. web-RSync handles this automatically:
        it SSHes into the source host and runs rsync from there, forwarding its SSH agent
        (<code>-A</code>) so the source can reach the destination without the private key leaving
        the server.
      </p>
      <p><strong>Prerequisites:</strong> deploy the server's public key to <em>both</em> hosts using
        the <strong>Deploy Key</strong> button on the Hosts page before running the task.</p>

      <h3>rsync Options</h3>
      <p>Raw flags passed directly to rsync. Common sets:</p>
      <table>
        <thead><tr><th>Use case</th><th>Options</th></tr></thead>
        <tbody>
          <tr><td>Standard archive</td><td><code>-avz</code></td></tr>
          <tr><td>Archive + delete removed files</td><td><code>-avz --delete</code></td></tr>
          <tr><td>Archive + hard links</td><td><code>-avzH</code></td></tr>
          <tr><td>Bandwidth-limited</td><td><code>-avz --bwlimit=5000</code></td></tr>
        </tbody>
      </table>
      <p>Use the <strong>Browse flags</strong> panel in the task form to explore ~60 available flags.</p>

      <h3>Dry Run</h3>
      <p>
        Click <strong>▶ Test Dry Run</strong> in the task form to validate your paths and options
        before saving. rsync runs with <code>--dry-run</code> — no files are transferred — and
        output streams live in the panel below the form.
      </p>
      <p>
        From the Tasks list, click <strong>Dry</strong> on a saved task to do the same on the
        persisted configuration.
      </p>

      <h3>Scheduling</h3>
      <p>Uses standard 5-field cron syntax: <code>minute hour day month weekday</code></p>
      <table>
        <thead><tr><th>Expression</th><th>Meaning</th></tr></thead>
        <tbody>
          <tr><td><code>0 2 * * *</code></td><td>Every day at 02:00</td></tr>
          <tr><td><code>0 */6 * * *</code></td><td>Every 6 hours</td></tr>
          <tr><td><code>30 1 * * 0</code></td><td>Every Sunday at 01:30</td></tr>
          <tr><td><code>0 0 1 * *</code></td><td>First of the month at midnight</td></tr>
        </tbody>
      </table>
      <p>Scheduled tasks only run when <strong>Enabled</strong> is checked.</p>

      <h3>Clone</h3>
      <p>
        <strong>Clone</strong> copies a task with schedule cleared and enabled set to false — safe
        to edit without affecting the original.
      </p>
    </div>

    <div class="card section">
      <h2>Hosts</h2>
      <p>
        A <strong>Host</strong> is a registered SSH target. You do <em>not</em> need to register a
        host to use it in a task — you can type <code>user@host:/path</code> directly. Hosts are
        only needed for the automated key-deployment feature.
      </p>

      <h3>Deploy Key</h3>
      <ol>
        <li>Go to <strong>Hosts</strong> and click <strong>+ New Host</strong>. Fill in name, hostname/IP, SSH port, and username.</li>
        <li>Click <strong>Deploy Key</strong> next to the host and enter the SSH password (used once, never stored).</li>
        <li>The server's public key is appended to <code>~/.ssh/authorized_keys</code> on the remote machine.</li>
        <li>rsync tasks to that host now authenticate without a password.</li>
      </ol>
      <p>The server's public key is shown at the top of the Hosts page and lives at <code>data/ssh/id_rsa.pub</code>.</p>
    </div>

    <div class="card section">
      <h2>Job History</h2>
      <p>
        Every run — manual, scheduled, or dry-run — creates a record with status, trigger, duration,
        and the full rsync log. Click any row to view its log. Running jobs stream output live via
        SSE; completed jobs load from disk.
      </p>
      <p>Statuses: <code>running</code> · <code>success</code> · <code>failed</code> · <code>cancelled</code></p>
    </div>

    <div class="card section">
      <h2>Dashboard</h2>
      <p>Shows a summary of recent runs, task counts, and quick-access buttons to trigger tasks manually.</p>
    </div>
  </div>
</template>

<style scoped>
.section { margin-bottom: 16px; }
.section h2 {
  font-size: 16px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #1e293b;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 6px;
}
.section h3 {
  font-size: 13px;
  font-weight: 700;
  margin: 16px 0 6px;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.section p, .section li {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0 0 8px;
}
.section ul, .section ol {
  padding-left: 20px;
  margin: 0 0 8px;
}
.section table {
  width: auto;
  margin: 8px 0 12px;
  font-size: 12px;
}
.section table th {
  background: #f3f4f6;
  font-weight: 600;
}
.section table th, .section table td {
  padding: 6px 12px;
}
.note {
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
  padding: 8px 12px !important;
  border-radius: 2px;
  margin: 8px 0 !important;
}
</style>
