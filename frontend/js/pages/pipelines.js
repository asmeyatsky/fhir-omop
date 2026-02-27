/**
 * Pipelines — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, formatNumber, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

const STAGES = ['extract', 'validate', 'transform', 'load'];

function stageProgress(pipeline) {
  if (!pipeline.stage_results || !pipeline.stage_results.length) {
    if (pipeline.status === 'running') {
      return `<div class="d-flex gap-1"><div class="flex-grow-1 rounded bg-secondary bg-opacity-25" style="height: 6px;"></div><div class="flex-grow-1 rounded bg-secondary bg-opacity-25" style="height: 6px;"></div><div class="flex-grow-1 rounded bg-secondary bg-opacity-25" style="height: 6px;"></div><div class="flex-grow-1 rounded bg-secondary bg-opacity-25" style="height: 6px;"></div></div>`;
    }
    return '';
  }
  const completed = pipeline.stage_results.map(s => s.stage);
  return `<div class="d-flex gap-1">${STAGES.map(s => {
    const done = completed.includes(s);
    const current = pipeline.current_stage === s;
    const cls = done ? 'bg-primary' : current ? 'bg-primary bg-opacity-50' : 'bg-secondary bg-opacity-25';
    return `<div class="flex-grow-1 rounded ${cls}" style="height: 6px;" title="${s}"></div>`;
  }).join('')}</div>`;
}

function pipelineDetail(p) {
  const stages = (p.stage_results || []).map(s => `
    <tr>
      <td class="text-capitalize fw-medium">${s.stage}</td>
      <td>${formatNumber(s.records_in)}</td>
      <td>${formatNumber(s.records_out)}</td>
      <td class="${s.error_count > 0 ? 'text-danger' : 'text-secondary'}">${formatNumber(s.error_count)}</td>
    </tr>
  `).join('');

  showModal(`
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h5 class="mb-0">${escapeHtml(p.name)}</h5>
      ${statusBadge(p.status)}
    </div>
    <div class="row g-3 small mb-3">
      <div class="col-6"><span class="text-secondary">Created:</span> ${formatDateTime(p.created_at)}</div>
      <div class="col-6"><span class="text-secondary">Started:</span> ${formatDateTime(p.started_at)}</div>
      <div class="col-6"><span class="text-secondary">Completed:</span> ${formatDateTime(p.completed_at)}</div>
      <div class="col-6"><span class="text-secondary">Records:</span> ${formatNumber(p.total_records)}</div>
    </div>
    ${p.error_message ? `<div class="alert alert-danger small mb-3">${escapeHtml(p.error_message)}</div>` : ''}
    ${stages ? `
      <p class="small fw-semibold text-secondary mb-2">Stage Results</p>
      <table class="table table-sm app-table">
        <thead><tr><th>Stage</th><th>In</th><th>Out</th><th>Errors</th></tr></thead>
        <tbody>${stages}</tbody>
      </table>
    ` : ''}
    <div class="d-flex justify-content-end mt-3">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
    </div>
  `);
}

export async function renderPipelines(root) {
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">Pipelines</h1>
        <p class="app-page-subtitle mb-0">FHIR-to-OMOP transformation pipelines</p>
      </div>
      <button type="button" id="create-pipeline-btn" class="btn btn-primary">
        <i class="bi bi-plus-lg me-2"></i>New Pipeline
      </button>
    </div>
    <div class="card app-card">
      <div class="card-body p-0" id="pipelines-table"></div>
    </div>
  `;

  let sources = [];
  let mappings = [];

  async function loadPipelines() {
    try {
      const pipelines = await api.get('/api/v1/pipelines');
      const el = document.getElementById('pipelines-table');
      if (!pipelines.length) {
        el.innerHTML = emptyState('No pipelines created yet');
        return;
      }
      el.innerHTML = `
        <div class="table-responsive">
          <table class="table app-table mb-0">
            <thead><tr><th>Name</th><th>Status</th><th>Progress</th><th>Records</th><th>Errors</th><th>Created</th></tr></thead>
            <tbody>
              ${pipelines.map(p => `
                <tr class="pipeline-row align-middle" role="button" data-id="${escapeHtml(p.id)}">
                  <td class="fw-medium">${escapeHtml(p.name)}</td>
                  <td>${statusBadge(p.status)}</td>
                  <td style="min-width: 120px;">${stageProgress(p)}</td>
                  <td>${formatNumber(p.total_records)}</td>
                  <td class="${p.total_errors > 0 ? 'text-danger' : 'text-secondary'}">${formatNumber(p.total_errors)}</td>
                  <td class="text-secondary small">${formatDateTime(p.created_at)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      el.querySelectorAll('.pipeline-row').forEach(row => {
        row.addEventListener('click', async () => {
          try {
            const p = await api.get(`/api/v1/pipelines/${row.dataset.id}`);
            pipelineDetail(p);
          } catch (err) {
            toast(err.message, 'error');
          }
        });
      });
    } catch (err) {
      toast('Failed to load pipelines', 'error');
    }
  }

  document.getElementById('create-pipeline-btn').addEventListener('click', async () => {
    try {
      [sources, mappings] = await Promise.all([
        api.get('/api/v1/sources'),
        api.get('/api/v1/mappings'),
      ]);
    } catch { /* use cached */ }
    const sourceOpts = sources.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
    const mappingOpts = mappings.map(m => `<option value="${m.id}">${escapeHtml(m.name)} (${m.source_resource} → ${m.target_table})</option>`).join('');

    showModal(`
      <h5 class="mb-4">Create Pipeline</h5>
      <form id="pipeline-form">
        <div class="mb-3">
          <label class="form-label">Pipeline Name</label>
          <input type="text" name="name" class="form-control" placeholder="e.g. Patient Data Import Q1" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Source Connection</label>
          <select name="source_connection_id" class="form-select" required>${sourceOpts || '<option disabled>No sources available</option>'}</select>
        </div>
        <div class="mb-3">
          <label class="form-label">Mapping Configurations</label>
          <select name="mapping_config_ids" class="form-select" multiple size="3" required>${mappingOpts || '<option disabled>No mappings available</option>'}</select>
          <p class="small text-muted mt-1 mb-0">Hold Ctrl/Cmd to select multiple</p>
        </div>
        <div class="mb-3">
          <label class="form-label">Target Connection String</label>
          <input type="text" name="target_connection_string" class="form-control" placeholder="postgresql://localhost:5432/omop" required>
        </div>
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Execute Pipeline</button>
        </div>
      </form>
    `);
    document.getElementById('pipeline-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.post('/api/v1/pipelines', {
          name: fd.get('name'),
          source_connection_id: fd.get('source_connection_id'),
          mapping_config_ids: fd.getAll('mapping_config_ids'),
          target_connection_string: fd.get('target_connection_string'),
        });
        closeModal();
        toast('Pipeline created and executing', 'success');
        loadPipelines();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  loadPipelines();
}
