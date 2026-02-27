/**
 * Audit log page (ADMIN/AUDITOR only).
 */
import { api } from '../core/api.js';
import { formatDateTime, toast, statusBadge, escapeHtml } from '../core/utils.js';

export async function renderAudit(root) {
  let filters = { event_type: '', actor_id: '', limit: 50, offset: 0 };

  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Log</h1>
        <p class="page-subtitle">System activity and compliance trail</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="card mb-6">
      <div class="card-body">
        <div class="flex flex-wrap gap-4 items-end">
          <div class="flex-1 min-w-[200px]">
            <label class="form-label">Event Type</label>
            <input type="text" id="filter-event" class="form-input" placeholder="e.g., auth.login, pipeline.execute">
          </div>
          <div class="flex-1 min-w-[200px]">
            <label class="form-label">Actor ID</label>
            <input type="text" id="filter-actor" class="form-input" placeholder="User ID">
          </div>
          <button id="apply-filters" class="btn btn-primary btn-sm">Apply Filters</button>
          <button id="clear-filters" class="btn btn-secondary btn-sm">Clear</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="text-sm text-gray-400" id="audit-count"></span>
        <div class="flex gap-2">
          <button id="prev-page" class="btn btn-ghost btn-sm" disabled>&larr; Previous</button>
          <button id="next-page" class="btn btn-ghost btn-sm">Next &rarr;</button>
        </div>
      </div>
      <div class="card-body p-0" id="audit-table"></div>
    </div>
  `;

  async function loadAudit() {
    try {
      const data = await api.get('/api/v1/audit', filters);
      const entries = data.entries || [];
      const total = data.total || 0;

      document.getElementById('audit-count').textContent = `Showing ${filters.offset + 1}–${Math.min(filters.offset + filters.limit, total)} of ${total} entries`;
      document.getElementById('prev-page').disabled = filters.offset === 0;
      document.getElementById('next-page').disabled = filters.offset + filters.limit >= total;

      const el = document.getElementById('audit-table');
      if (!entries.length) {
        el.innerHTML = '<div class="empty-state py-8"><p class="text-gray-500 text-sm">No audit entries found</p></div>';
        return;
      }

      el.innerHTML = `
        <table class="data-table">
          <thead>
            <tr><th>Timestamp</th><th>Event</th><th>Action</th><th>Actor</th><th>Resource</th><th>Status</th><th>Integrity</th></tr>
          </thead>
          <tbody>
            ${entries.map(e => `
              <tr>
                <td class="text-xs text-gray-400 whitespace-nowrap">${formatDateTime(e.timestamp)}</td>
                <td><span class="badge badge-info">${escapeHtml(e.event_type)}</span></td>
                <td class="text-gray-300 text-xs">${escapeHtml(e.action)}</td>
                <td class="text-xs text-gray-400">${e.actor_email || e.actor_id || '—'}</td>
                <td class="text-xs font-mono text-gray-500">${e.resource_type ? `${e.resource_type}/${(e.resource_id || '').substring(0, 8)}` : '—'}</td>
                <td>${e.http_status ? statusBadge(e.http_status < 400 ? 'completed' : 'error') : '—'}</td>
                <td>
                  <button class="btn btn-ghost btn-sm verify-btn" data-id="${e.id}" title="Verify integrity">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;

      // Verify buttons
      el.querySelectorAll('.verify-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          try {
            const res = await api.get(`/api/v1/audit/${btn.dataset.id}/verify`);
            toast(res.valid ? 'Integrity verified' : 'Integrity check FAILED', res.valid ? 'success' : 'error');
          } catch (err) {
            toast(err.message, 'error');
          }
        });
      });
    } catch (err) {
      toast('Failed to load audit log', 'error');
    }
  }

  // Filter handlers
  document.getElementById('apply-filters').addEventListener('click', () => {
    filters.event_type = document.getElementById('filter-event').value;
    filters.actor_id = document.getElementById('filter-actor').value;
    filters.offset = 0;
    loadAudit();
  });

  document.getElementById('clear-filters').addEventListener('click', () => {
    document.getElementById('filter-event').value = '';
    document.getElementById('filter-actor').value = '';
    filters = { event_type: '', actor_id: '', limit: 50, offset: 0 };
    loadAudit();
  });

  document.getElementById('prev-page').addEventListener('click', () => {
    filters.offset = Math.max(0, filters.offset - filters.limit);
    loadAudit();
  });

  document.getElementById('next-page').addEventListener('click', () => {
    filters.offset += filters.limit;
    loadAudit();
  });

  loadAudit();
}
