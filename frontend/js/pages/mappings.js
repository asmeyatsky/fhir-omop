/**
 * Mapping Templates & Configurations — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderMappings(root) {
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">Mapping Configurations</h1>
        <p class="app-page-subtitle mb-0">FHIR R4 to OMOP CDM v5.4 field mappings</p>
      </div>
      <button type="button" id="create-mapping-btn" class="btn btn-primary">
        <i class="bi bi-plus-lg me-2"></i>Create Mapping
      </button>
    </div>
    <p class="small text-secondary text-uppercase fw-semibold mb-3">Available Templates</p>
    <div class="row g-3 mb-4" id="templates-grid"></div>
    <div class="card app-card">
      <div class="card-header">Active Configurations</div>
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

      const tplGrid = document.getElementById('templates-grid');
      if (!tpls.length) {
        tplGrid.innerHTML = '<div class="col-12 text-secondary small">No templates available</div>';
      } else {
        tplGrid.innerHTML = tpls.map(t => `
          <div class="col-12 col-md-6 col-lg-4">
            <div class="card app-card h-100">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <h6 class="mb-0 fw-semibold">${escapeHtml(t.name)}</h6>
                  <span class="badge bg-primary">${t.field_count} fields</span>
                </div>
                <p class="small text-secondary mb-2">${escapeHtml(t.description)}</p>
                <div class="small text-secondary">
                  <code>${escapeHtml(t.source_resource)}</code> <i class="bi bi-arrow-right mx-1"></i> <code>${escapeHtml(t.target_table)}</code>
                </div>
              </div>
            </div>
          </div>
        `).join('');
      }

      const tbl = document.getElementById('mappings-table');
      if (!configs.length) {
        tbl.innerHTML = emptyState('No mapping configurations created yet');
      } else {
        tbl.innerHTML = `
          <div class="table-responsive">
            <table class="table app-table mb-0">
              <thead><tr><th>Name</th><th>Source</th><th>Target</th><th>Fields</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>
                ${configs.map(c => `
                  <tr>
                    <td class="fw-medium">${escapeHtml(c.name)}</td>
                    <td class="small"><code>${escapeHtml(c.source_resource)}</code></td>
                    <td class="small"><code>${escapeHtml(c.target_table)}</code></td>
                    <td>${c.field_count}</td>
                    <td>${statusBadge(c.status)}</td>
                    <td class="text-secondary small">${formatDateTime(c.created_at)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
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
      <h5 class="mb-4">Create Mapping Configuration</h5>
      <form id="mapping-form">
        <div class="mb-3">
          <label class="form-label">Configuration Name</label>
          <input type="text" name="name" class="form-control" placeholder="e.g. Patient Demographics v1" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Template</label>
          <select name="template_id" class="form-select" required>${opts}</select>
        </div>
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Create</button>
        </div>
      </form>
    `);
    document.getElementById('mapping-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await api.post('/api/v1/mappings', Object.fromEntries(new FormData(e.target)));
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
