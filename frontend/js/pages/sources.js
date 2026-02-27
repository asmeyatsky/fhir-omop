/**
 * FHIR Source Connections — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderSources(root) {
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">FHIR Source Connections</h1>
        <p class="app-page-subtitle mb-0">Manage connections to FHIR R4 servers</p>
      </div>
      <button type="button" id="add-source-btn" class="btn btn-primary">
        <i class="bi bi-plus-lg me-2"></i>Add Source
      </button>
    </div>
    <div class="card app-card">
      <div class="card-body p-0" id="sources-table"></div>
    </div>
  `;

  async function loadSources() {
    try {
      const sources = await api.get('/api/v1/sources');
      const el = document.getElementById('sources-table');
      if (!sources.length) {
        el.innerHTML = emptyState('No FHIR source connections configured yet');
        return;
      }
      el.innerHTML = `
        <div class="table-responsive">
          <table class="table app-table mb-0">
            <thead>
              <tr><th>Name</th><th>Server Type</th><th>Base URL</th><th>Auth</th><th>Status</th><th>Last Tested</th><th></th></tr>
            </thead>
            <tbody>
              ${sources.map(s => `
                <tr>
                  <td class="fw-medium">${escapeHtml(s.name)}</td>
                  <td><span class="badge bg-primary">${escapeHtml(s.server_type)}</span></td>
                  <td class="text-secondary small text-truncate" style="max-width: 220px;">${escapeHtml(s.base_url)}</td>
                  <td class="text-secondary">${escapeHtml(s.auth_method)}</td>
                  <td>${statusBadge(s.status)}</td>
                  <td class="text-secondary small">${formatDateTime(s.last_tested_at)}</td>
                  <td>
                    <button type="button" class="btn btn-sm btn-outline-primary test-source-btn" data-id="${escapeHtml(s.id)}">
                      <i class="bi bi-lightning"></i> Test
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      el.querySelectorAll('.test-source-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
          try {
            const result = await api.post(`/api/v1/sources/${btn.dataset.id}/test`);
            toast(`Connection ${result.status}`, result.status === 'connected' ? 'success' : 'error');
            loadSources();
          } catch (err) {
            toast(err.message, 'error');
          } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-lightning"></i> Test';
          }
        });
      });
    } catch (err) {
      toast('Failed to load sources', 'error');
    }
  }

  document.getElementById('add-source-btn').addEventListener('click', () => {
    showModal(`
      <h5 class="mb-4">Add FHIR Source Connection</h5>
      <form id="source-form">
        <div class="mb-3">
          <label class="form-label">Connection Name</label>
          <input type="text" name="name" class="form-control" placeholder="e.g. HAPI FHIR Dev Server" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Base URL</label>
          <input type="url" name="base_url" class="form-control" placeholder="https://hapi.fhir.org/baseR4" required>
        </div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Server Type</label>
            <select name="server_type" class="form-select" required>
              <option value="hapi">HAPI FHIR</option>
              <option value="cerner">Cerner</option>
              <option value="epic">Epic</option>
              <option value="generic">Generic R4</option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">Auth Method</label>
            <select name="auth_method" class="form-select" required>
              <option value="none">None</option>
              <option value="api_key">API Key</option>
              <option value="oauth2">OAuth 2.0</option>
              <option value="basic">Basic Auth</option>
            </select>
          </div>
        </div>
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Create Connection</button>
        </div>
      </form>
    `);
    document.getElementById('source-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await api.post('/api/v1/sources', Object.fromEntries(new FormData(e.target)));
        closeModal();
        toast('Source connection created', 'success');
        loadSources();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  loadSources();
}
