<template>
  <div class="page">
    <h1 class="page-title">Help</h1>

    <div class="card section">
      <h2>What is web-RSync?</h2>
      <p>
        web-RSync is a browser-based manager for <strong>rsync</strong> jobs. It lets you define,
        schedule, and monitor file-synchronization tasks between machines — without touching the
        command line after the initial setup.
      </p>
      <p>Typical use cases:</p>
      <ul>
        <li>Automated nightly backups from a server to a NAS</li>
        <li>Keeping two remote machines in sync on a schedule</li>
        <li>One-shot manual transfers with real-time progress</li>
        <li>Validating rsync options with a dry-run before committing</li>
      </ul>

      <h3>How it works</h3>
      <p>
        All rsync processes run <strong>on the web-RSync server</strong>, not in your browser.
        Your browser is only a control panel — it sends instructions and displays logs, but is
        never involved in the actual file transfer.
      </p>
      <p>
        When running in Docker (the standard deployment), <strong>"local" paths refer to the
        filesystem inside the Docker container</strong>, not the machine where you open the
        browser. A path like <code>/data/backups/</code> must exist inside the container.
        To expose host directories, mount them in <code>docker-compose.yml</code>:
      </p>
      <pre class="code-block">volumes:
  - ./data:/data          # already mounted (DB, logs, SSH keys)
  - /mnt/nas:/mnt/nas     # add any host path you want rsync to reach</pre>
      <p>
        If both endpoints are remote SSH hosts, no volume mounts are needed — web-RSync
        SSHes out and rsync runs between the two remote machines.
      </p>
    </div>

    <div class="card section">
      <h2>Tasks</h2>
      <p>
        A <strong>Task</strong> defines one rsync job: source path, destination path, rsync options,
        and an optional cron schedule.
      </p>

      <h3>Path formats</h3>
      <p>
        A bare path starting with <code>/</code> is <strong>local to the web-RSync server</strong>
        (i.e. inside the Docker container). A path containing <code>user@host:</code> is a remote
        SSH endpoint. Your browser machine is never a source or destination.
      </p>
      <table>
        <thead><tr><th>Scenario</th><th>Source example</th><th>Destination example</th></tr></thead>
        <tbody>
          <tr>
            <td>Server → server<br><small style="color:#6b7280">(both paths local to the container)</small></td>
            <td><code>/mnt/nas/source/</code></td>
            <td><code>/mnt/nas/backup/</code></td>
          </tr>
          <tr>
            <td>Server → remote</td>
            <td><code>/mnt/nas/source/</code></td>
            <td><code>user@host2:/backup/</code></td>
          </tr>
          <tr>
            <td>Remote → server</td>
            <td><code>user@host1:/data/</code></td>
            <td><code>/mnt/nas/backup/</code></td>
          </tr>
          <tr>
            <td>Remote → remote</td>
            <td><code>user@host1:/data/</code></td>
            <td><code>user@host2:/backup/</code></td>
          </tr>
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
      <p>
        Raw flags passed directly to rsync. The field is <strong>not</strong> processed by a shell —
        constructs like <code>$(date +%F)</code> are passed literally and will not expand.
        Use the <strong>Browse flags</strong> panel in the task form to explore ~60 available flags.
      </p>

      <p style="font-weight:600;margin-top:12px;margin-bottom:4px">Common sets</p>
      <table>
        <thead><tr><th>Use case</th><th>Options</th><th>Notes</th></tr></thead>
        <tbody>
          <tr><td>Standard archive</td><td><code>-avz</code></td><td>Recursive, preserves permissions/times, compresses in transit</td></tr>
          <tr><td>Strict mirror</td><td><code>-avz --delete</code></td><td>Removes destination files that no longer exist at source</td></tr>
          <tr><td>Preserve hard links</td><td><code>-avzH</code></td><td>Important for deduplicated backups and system directories</td></tr>
          <tr><td>Bandwidth throttle</td><td><code>-avz --bwlimit=50000</code></td><td>Limit throughput; value is KB/s (50000 ≈ 50 MB/s)</td></tr>
        </tbody>
      </table>

      <p style="font-weight:600;margin-top:12px;margin-bottom:4px">Homelab scenarios</p>
      <table>
        <thead><tr><th>Use case</th><th>Options</th><th>Notes</th></tr></thead>
        <tbody>
          <tr>
            <td>VM / disk images</td>
            <td><code>-av --sparse</code></td>
            <td>Preserves sparse regions in qcow2, raw images, and LXC rootfs. Drop <code>-z</code> — compressing binary images wastes CPU without saving space</td>
          </tr>
          <tr>
            <td>VM images + resumable</td>
            <td><code>-av --sparse --inplace --partial</code></td>
            <td>In-place writes halve peak disk usage; <code>--partial</code> lets the next run resume an interrupted transfer</td>
          </tr>
          <tr>
            <td>Cross-system (different UIDs)</td>
            <td><code>-avz --numeric-ids</code></td>
            <td>Uses numeric UID/GID instead of names — essential when syncing between Proxmox nodes or containers with different user databases</td>
          </tr>
          <tr>
            <td>Docker volumes / full permissions</td>
            <td><code>-avzAX</code></td>
            <td>Adds ACL (<code>-A</code>) and extended attribute (<code>-X</code>) preservation — important for Docker named volumes and system directories</td>
          </tr>
          <tr>
            <td>Stay within one filesystem</td>
            <td><code>-avz -x</code></td>
            <td>Don't cross mount points — prevents accidentally syncing bind-mounted paths or overlapping volumes</td>
          </tr>
          <tr>
            <td>Checksum-based comparison</td>
            <td><code>-avz --checksum</code></td>
            <td>Compares by file content instead of mtime+size — slower but reliable after a restore or when clocks differ between hosts</td>
          </tr>
          <tr>
            <td>Skip large files</td>
            <td><code>-avz --max-size=500m</code></td>
            <td>Avoid accidentally syncing large ISOs or VM disk images; supports <code>k</code>, <code>m</code>, <code>g</code> suffixes</td>
          </tr>
          <tr>
            <td>Exclude temp / cache</td>
            <td><code>-avz --exclude='*.tmp' --exclude='*.log'</code></td>
            <td>Chain as many <code>--exclude</code> flags as needed; patterns are matched against the relative path</td>
          </tr>
          <tr>
            <td>Resumable over unreliable links</td>
            <td><code>-avz --partial</code></td>
            <td>Keeps partially transferred files so the next run continues from where it stopped — useful for large files over VPN or WAN</td>
          </tr>
          <tr>
            <td>Live progress (large transfers)</td>
            <td><code>-avz --info=progress2</code></td>
            <td>Compact single-line progress — cleaner than <code>-v</code> when transferring thousands of files</td>
          </tr>
        </tbody>
      </table>

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
.code-block {
  background: #f3f4f6;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 12px;
  font-family: monospace;
  margin: 6px 0 10px;
  white-space: pre;
  overflow-x: auto;
}
</style>
