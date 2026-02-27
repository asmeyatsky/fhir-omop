/**
 * FHIR Source Connections page.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderSources(root) {
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">FHIR Source Connections</h1>
        <p class="page-subtitle">Manage connections to FHIR R4 servers</p>
      </div>
      <button id="add-source-btn" class="btn btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Add Source
      </button>
    </div>
    <div class="card">
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
        <table class="data-table">
          <thead>
            <tr><th>Name</th><th>Server Type</th><th>Base URL</th><th>Auth</th><th>Status</th><th>Last Tested</th><th>Actions</th></tr>
          </thead>
          <tbody>
            ${sources.map(s => `
              <tr>
                <td class="font-medium text-gray-200">${escapeHtml(s.name)}</td>
                <td><span class="badge badge-teal">${s.server_type}</span></td>
                <td class="text-xs font-mono text-gray-400 max-w-[200px] truncate">${escapeHtml(s.base_url)}</td>
                <td class="text-gray-400">${s.auth_method}</td>
                <td>${statusBadge(s.status)}</td>
                <td class="text-gray-400 text-xs">${formatDateTime(s.last_tested_at)}</td>
                <td>
                  <button class="btn btn-ghost btn-sm test-source-btn" data-id="${s.id}">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    Test
                  </button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;

      // Test connection handlers
      el.querySelectorAll('.test-source-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          btn.disabled = true;
          btn.textContent = 'Testing...';
          try {
            const result = await api.post(`/api/v1/sources/${btn.dataset.id}/test`);
            toast(`Connection ${result.status}`, result.status === 'connected' ? 'success' : 'error');
            loadSources();
          } catch (err) {
            toast(err.message, 'error');
          } finally {
            btn.disabled = false;
          }
        });
      });
    } catch (err) {
      toast('Failed to load sources', 'error');
    }
  }

  // Add source modal
  document.getElementById('add-source-btn').addEventListener('click', () => {
    showModal(`
      <div class="p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Add FHIR Source Connection</h3>
        <form id="source-form" class="space-y-4">
          <div>
            <label class="form-label">Connection Name</label>
            <input type="text" name="name" class="form-input" placeholder="e.g., HAPI FHIR Dev Server" required>
          </div>
          <div>
            <label class="form-label">Base URL</label>
            <input type="url" name="base_url" class="form-input" placeholder="https://hapi.fhir.org/baseR4" required>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Server Type</label>
              <select name="server_type" class="form-select" required>
                <option value="hapi">HAPI FHIR</option>
                <option value="cerner">Cerner</option>
                <option value="epic">Epic</option>
                <option value="generic">Generic R4</option>
              </select>
            </div>
            <div>
              <label class="form-label">Auth Method</label>
              <select name="auth_method" class="form-select" required>
                <option value="none">None</option>
                <option value="api_key">API Key</option>
                <option value="oauth2">OAuth 2.0</option>
                <option value="basic">Basic Auth</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Create Connection</button>
          </div>
        </form>
      </div>
    `);

    document.getElementById('source-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.post('/api/v1/sources', Object.fromEntries(fd));
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
