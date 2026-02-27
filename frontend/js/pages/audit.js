/**
 * Audit Log (ADMIN/AUDITOR) — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { formatDateTime, toast, statusBadge, escapeHtml } from '../core/utils.js';

export async function renderAudit(root) {
  let filters = { event_type: '', actor_id: '', limit: 50, offset: 0 };

  root.innerHTML = `
    <div class="app-page-header">
      <h1 class="app-page-title">Audit Log</h1>
      <p class="app-page-subtitle mb-0">System activity and compliance trail</p>
    </div>
    <div class="card app-card mb-4">
      <div class="card-body">
        <div class="row g-3 align-items-end">
          <div class="col-12 col-md-4">
            <label class="form-label">Event Type</label>
            <input type="text" id="filter-event" class="form-control" placeholder="e.g. auth.login">
          </div>
          <div class="col-12 col-md-4">
            <label class="form-label">Actor ID</label>
            <input type="text" id="filter-actor" class="form-control" placeholder="User ID">
          </div>
          <div class="col-12 col-md-4 d-flex gap-2">
            <button type="button" id="apply-filters" class="btn btn-primary">Apply</button>
            <button type="button" id="clear-filters" class="btn btn-outline-secondary">Clear</button>
          </div>
        </div>
      </div>
    </div>
    <div class="card app-card">
      <div class="card-header d-flex justify-content-between align-items-center flex-wrap gap-2">
        <span class="small text-secondary" id="audit-count"></span>
        <div class="d-flex gap-2">
          <button type="button" id="prev-page" class="btn btn-sm btn-outline-secondary" disabled>Previous</button>
          <button type="button" id="next-page" class="btn btn-sm btn-outline-secondary">Next</button>
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
        el.innerHTML = '<div class="p-5 text-center text-secondary small">No audit entries found</div>';
        return;
      }
      el.innerHTML = `
        <div class="table-responsive">
          <table class="table app-table mb-0">
            <thead>
              <tr><th>Timestamp</th><th>Event</th><th>Action</th><th>Actor</th><th>Resource</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              ${entries.map(e => `
                <tr>
                  <td class="small text-secondary">${formatDateTime(e.timestamp)}</td>
                  <td><span class="badge badge-app-info">${escapeHtml(e.event_type)}</span></td>
                  <td class="small">${escapeHtml(e.action)}</td>
                  <td class="small text-secondary">${escapeHtml(e.actor_email || e.actor_id || '—')}</td>
                  <td class="small font-monospace">${e.resource_type ? `${e.resource_type}/${(e.resource_id || '').substring(0, 8)}` : '—'}</td>
                  <td>${e.http_status ? statusBadge(e.http_status < 400 ? 'completed' : 'error') : '—'}</td>
                  <td><button type="button" class="btn btn-sm btn-outline-primary verify-btn" data-id="${escapeHtml(e.id)}" title="Verify"><i class="bi bi-shield-check"></i></button></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      el.querySelectorAll('.verify-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          try {
            const res = await api.get(`/api/v1/audit/${btn.dataset.id}/verify`);
            toast(res.valid ? 'Integrity verified' : 'Verification failed', res.valid ? 'success' : 'error');
          } catch (err) {
            toast(err.message, 'error');
          }
        });
      });
    } catch (err) {
      toast('Failed to load audit log', 'error');
    }
  }

  document.getElementById('apply-filters').addEventListener('click', () => {
    filters.event_type = document.getElementById('filter-event').value.trim();
    filters.actor_id = document.getElementById('filter-actor').value.trim();
    filters.offset = 0;
    loadAudit();
  });
  document.getElementById('clear-filters').addEventListener('click', () => {
    document.getElementById('filter-event').value = '';
    document.getElementById('filter-actor').value = '';
    filters.event_type = '';
    filters.actor_id = '';
    filters.offset = 0;
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
