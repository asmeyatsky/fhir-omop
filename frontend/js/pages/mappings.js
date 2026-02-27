/**
 * Mapping Templates & Configurations page.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderMappings(root) {
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Mapping Configurations</h1>
        <p class="page-subtitle">FHIR R4 to OMOP CDM v5.4 field mappings</p>
      </div>
      <button id="create-mapping-btn" class="btn btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Create Mapping
      </button>
    </div>

    <!-- Templates -->
    <div class="mb-8">
      <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Available Templates</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="templates-grid"></div>
    </div>

    <!-- Configs -->
    <div class="card">
      <div class="card-header">
        <h3 class="text-sm font-semibold text-white">Active Configurations</h3>
      </div>
      <div class="card-body p-0" id="mappings-table"></div>
    </div>
  `;

  let templates = [];

  async function load() {
    try {
      const [tpls, configs] = await Promise.all([
        api.get('/api/v1/mappings/templates'),
        api.get('/api/v1/mappings'),
      ]);
      templates = tpls;

      // Templates grid
      const tplGrid = document.getElementById('templates-grid');
      if (!tpls.length) {
        tplGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-3">No templates available</p>';
      } else {
        tplGrid.innerHTML = tpls.map(t => `
          <div class="card p-4 hover:border-teal-500/30 transition-colors">
            <div class="flex items-start justify-between mb-2">
              <h4 class="text-sm font-semibold text-white">${escapeHtml(t.name)}</h4>
              <span class="badge badge-teal">${t.field_count} fields</span>
            </div>
            <p class="text-xs text-gray-400 mb-3">${escapeHtml(t.description)}</p>
            <div class="flex items-center gap-3 text-xs text-gray-500">
              <span class="font-mono">${t.source_resource}</span>
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
              <span class="font-mono">${t.target_table}</span>
            </div>
          </div>
        `).join('');
      }

      // Configs table
      const tbl = document.getElementById('mappings-table');
      if (!configs.length) {
        tbl.innerHTML = emptyState('No mapping configurations created yet');
      } else {
        tbl.innerHTML = `
          <table class="data-table">
            <thead><tr><th>Name</th><th>Source</th><th>Target</th><th>Fields</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>
              ${configs.map(c => `
                <tr>
                  <td class="font-medium text-gray-200">${escapeHtml(c.name)}</td>
                  <td class="font-mono text-xs text-gray-400">${c.source_resource}</td>
                  <td class="font-mono text-xs text-gray-400">${c.target_table}</td>
                  <td>${c.field_count}</td>
                  <td>${statusBadge(c.status)}</td>
                  <td class="text-gray-400 text-xs">${formatDateTime(c.created_at)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }
    } catch (err) {
      toast('Failed to load mappings', 'error');
    }
  }

  document.getElementById('create-mapping-btn').addEventListener('click', () => {
    const opts = templates.map(t =>
      `<option value="${t.template_id}">${escapeHtml(t.name)} (${t.source_resource} → ${t.target_table})</option>`
    ).join('');

    showModal(`
      <div class="p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Create Mapping Configuration</h3>
        <form id="mapping-form" class="space-y-4">
          <div>
            <label class="form-label">Configuration Name</label>
            <input type="text" name="name" class="form-input" placeholder="e.g., Patient Demographics v1" required>
          </div>
          <div>
            <label class="form-label">Template</label>
            <select name="template_id" class="form-select" required>${opts}</select>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    `);

    document.getElementById('mapping-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.post('/api/v1/mappings', Object.fromEntries(fd));
        closeModal();
        toast('Mapping configuration created', 'success');
        load();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  load();
}
