/**
 * Pipeline execution and monitoring page.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, formatNumber, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

const STAGES = ['extract', 'validate', 'transform', 'load'];

function stageProgress(pipeline) {
  if (!pipeline.stage_results || !pipeline.stage_results.length) {
    if (pipeline.status === 'running') {
      return `<div class="flex gap-1 mt-2">${STAGES.map(() =>
        `<div class="h-1.5 flex-1 bg-surface-muted rounded-full overflow-hidden"><div class="h-full bg-brand/40 animate-pulse-glow rounded-full w-full"></div></div>`
      ).join('')}</div>`;
    }
    return '';
  }
  const completed = pipeline.stage_results.map(s => s.stage);
  return `<div class="flex gap-1 mt-2">${STAGES.map(s => {
    const done = completed.includes(s);
    const current = pipeline.current_stage === s;
    const cls = done ? 'bg-brand' : current ? 'bg-brand/60 animate-pulse-glow' : 'bg-ink-200';
    return `<div class="h-1.5 flex-1 ${cls} rounded-full" title="${s}"></div>`;
  }).join('')}</div>`;
}

function pipelineDetail(p) {
  const stages = (p.stage_results || []).map(s => `
    <tr>
      <td class="font-medium text-ink-800 capitalize">${s.stage}</td>
      <td>${formatNumber(s.records_in)}</td>
      <td>${formatNumber(s.records_out)}</td>
      <td class="${s.error_count > 0 ? 'text-red-600' : 'text-ink-500'}">${formatNumber(s.error_count)}</td>
    </tr>
  `).join('');

  showModal(`
    <div class="p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-ink-900">${escapeHtml(p.name)}</h3>
        ${statusBadge(p.status)}
      </div>
      <div class="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div><span class="text-ink-500">Created:</span> <span class="text-ink-800">${formatDateTime(p.created_at)}</span></div>
        <div><span class="text-ink-500">Started:</span> <span class="text-ink-800">${formatDateTime(p.started_at)}</span></div>
        <div><span class="text-ink-500">Completed:</span> <span class="text-ink-800">${formatDateTime(p.completed_at)}</span></div>
        <div><span class="text-ink-500">Records:</span> <span class="text-ink-800">${formatNumber(p.total_records)}</span></div>
      </div>
      ${p.error_message ? `<div class="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-700">${escapeHtml(p.error_message)}</div>` : ''}
      ${stages ? `
        <h4 class="text-sm font-medium text-ink-600 mb-2">Stage Results</h4>
        <table class="data-table">
          <thead><tr><th>Stage</th><th>In</th><th>Out</th><th>Errors</th></tr></thead>
          <tbody>${stages}</tbody>
        </table>
      ` : ''}
      <div class="flex justify-end mt-4">
        <button class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Close</button>
      </div>
    </div>
  `);
}

export async function renderPipelines(root) {
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Pipelines</h1>
        <p class="page-subtitle">FHIR-to-OMOP transformation pipelines</p>
      </div>
      <button id="create-pipeline-btn" class="btn btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        New Pipeline
      </button>
    </div>
    <div class="card">
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
        <table class="data-table">
          <thead><tr><th>Name</th><th>Status</th><th>Progress</th><th>Records</th><th>Errors</th><th>Created</th></tr></thead>
          <tbody>
            ${pipelines.map(p => `
              <tr class="cursor-pointer pipeline-row" data-id="${p.id}">
                <td class="font-medium text-ink-800">${escapeHtml(p.name)}</td>
                <td>${statusBadge(p.status)}</td>
                <td class="w-32">${stageProgress(p)}</td>
                <td>${formatNumber(p.total_records)}</td>
                <td class="${p.total_errors > 0 ? 'text-red-600' : 'text-ink-500'}">${formatNumber(p.total_errors)}</td>
                <td class="text-ink-500 text-xs">${formatDateTime(p.created_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
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
    // Load sources and mappings for the form
    try {
      [sources, mappings] = await Promise.all([
        api.get('/api/v1/sources'),
        api.get('/api/v1/mappings'),
      ]);
    } catch { /* use cached */ }

    const sourceOpts = sources.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
    const mappingOpts = mappings.map(m => `<option value="${m.id}">${escapeHtml(m.name)} (${m.source_resource} → ${m.target_table})</option>`).join('');

    showModal(`
      <div class="p-6">
        <h3 class="text-lg font-semibold text-ink-900 mb-4">Create Pipeline</h3>
        <form id="pipeline-form" class="space-y-4">
          <div>
            <label class="form-label">Pipeline Name</label>
            <input type="text" name="name" class="form-input" placeholder="e.g., Patient Data Import Q1" required>
          </div>
          <div>
            <label class="form-label">Source Connection</label>
            <select name="source_connection_id" class="form-select" required>${sourceOpts || '<option disabled>No sources available</option>'}</select>
          </div>
          <div>
            <label class="form-label">Mapping Configurations</label>
            <select name="mapping_config_ids" class="form-select" multiple required size="3">${mappingOpts || '<option disabled>No mappings available</option>'}</select>
            <p class="text-xs text-ink-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
          </div>
          <div>
            <label class="form-label">Target Connection String</label>
            <input type="text" name="target_connection_string" class="form-input" placeholder="postgresql://localhost:5432/omop" required>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Execute Pipeline</button>
          </div>
        </form>
      </div>
    `);

    document.getElementById('pipeline-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const data = {
        name: fd.get('name'),
        source_connection_id: fd.get('source_connection_id'),
        mapping_config_ids: fd.getAll('mapping_config_ids'),
        target_connection_string: fd.get('target_connection_string'),
      };
      try {
        await api.post('/api/v1/pipelines', data);
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
