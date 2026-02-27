/**
 * Dashboard — KPI cards, recent pipelines, sources. Bootstrap 5 layout.
 */
import { api } from '../core/api.js';
import { currentUser } from '../core/auth.js';
import { formatNumber, statusBadge, timeAgo, loadingCards, toast } from '../core/utils.js';

export async function renderDashboard(root) {
  const user = currentUser();
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">Dashboard</h1>
        <p class="app-page-subtitle mb-0">Welcome back, ${escapeHtml(user?.email || 'User')}</p>
      </div>
      <span id="health-indicator" class="badge badge-app-neutral">Checking…</span>
    </div>

    <div class="row g-4 mb-4" id="kpi-grid">
      ${loadingCards(4)}
    </div>

    <div class="row g-4">
      <div class="col-12 col-xl-6">
        <div class="card app-card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span>Recent Pipelines</span>
            <a href="#/pipelines" class="btn btn-sm btn-link link-primary text-decoration-none p-0">View all</a>
          </div>
          <div class="card-body p-0" id="recent-pipelines"></div>
        </div>
      </div>
      <div class="col-12 col-xl-6">
        <div class="card app-card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span>FHIR Source Connections</span>
            <a href="#/sources" class="btn btn-sm btn-link link-primary text-decoration-none p-0">View all</a>
          </div>
          <div class="card-body p-0" id="recent-sources"></div>
        </div>
      </div>
    </div>
  `;

  const [healthRes, sourcesRes, pipelinesRes] = await Promise.allSettled([
    fetch('/health').then(r => r.json()),
    api.get('/api/v1/sources').catch(() => []),
    api.get('/api/v1/pipelines').catch(() => []),
  ]);

  const health = healthRes.status === 'fulfilled' ? healthRes.value : null;
  const sources = sourcesRes.status === 'fulfilled' ? sourcesRes.value : [];
  const pipelines = pipelinesRes.status === 'fulfilled' ? pipelinesRes.value : [];

  const hi = document.getElementById('health-indicator');
  hi.className = health?.status === 'healthy' ? 'badge badge-app-success' : 'badge badge-app-danger';
  hi.textContent = health?.status === 'healthy' ? 'System healthy' : 'System degraded';

  const completedPipelines = pipelines.filter(p => p.status === 'completed').length;
  const totalRecords = pipelines.reduce((sum, p) => sum + (p.total_records || 0), 0);

  document.getElementById('kpi-grid').innerHTML = `
    <div class="col-12 col-sm-6 col-xl-3">
      <div class="app-stat-card h-100">
        <div class="app-stat-icon bg-primary bg-opacity-10 text-primary mb-2"><i class="bi bi-link-45deg"></i></div>
        <div class="app-stat-value">${formatNumber(sources.length)}</div>
        <div class="app-stat-label">FHIR Sources</div>
      </div>
    </div>
    <div class="col-12 col-sm-6 col-xl-3">
      <div class="app-stat-card h-100">
        <div class="app-stat-icon bg-primary bg-opacity-10 text-primary mb-2"><i class="bi bi-lightning"></i></div>
        <div class="app-stat-value">${formatNumber(pipelines.length)}</div>
        <div class="app-stat-label">Total Pipelines</div>
      </div>
    </div>
    <div class="col-12 col-sm-6 col-xl-3">
      <div class="app-stat-card h-100">
        <div class="app-stat-icon bg-success bg-opacity-10 text-success mb-2"><i class="bi bi-check-circle"></i></div>
        <div class="app-stat-value">${formatNumber(completedPipelines)}</div>
        <div class="app-stat-label">Completed Runs</div>
      </div>
    </div>
    <div class="col-12 col-sm-6 col-xl-3">
      <div class="app-stat-card h-100">
        <div class="app-stat-icon bg-primary bg-opacity-10 text-primary mb-2"><i class="bi bi-database"></i></div>
        <div class="app-stat-value">${formatNumber(totalRecords)}</div>
        <div class="app-stat-label">Records Transformed</div>
      </div>
    </div>
  `;

  const pipelinesEl = document.getElementById('recent-pipelines');
  if (pipelines.length === 0) {
    pipelinesEl.innerHTML = '<div class="p-4 text-center text-secondary small">No pipelines yet. <a href="#/pipelines" class="link-primary">Create one</a>.</div>';
  } else {
    const rows = pipelines.slice(0, 5).map(p => `
      <tr class="align-middle">
        <td><a href="#/pipelines" class="text-decoration-none text-dark fw-medium">${escapeHtml(p.name)}</a></td>
        <td>${statusBadge(p.status)}</td>
        <td class="text-secondary">${formatNumber(p.total_records)}</td>
        <td class="text-secondary small">${timeAgo(p.created_at)}</td>
      </tr>
    `).join('');
    pipelinesEl.innerHTML = `
      <table class="table app-table mb-0">
        <thead><tr><th>Name</th><th>Status</th><th>Records</th><th>Created</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  const sourcesEl = document.getElementById('recent-sources');
  if (sources.length === 0) {
    sourcesEl.innerHTML = '<div class="p-4 text-center text-secondary small">No sources configured. <a href="#/sources" class="link-primary">Add a source</a>.</div>';
  } else {
    const rows = sources.slice(0, 5).map(s => `
      <tr class="align-middle">
        <td><a href="#/sources" class="text-decoration-none text-dark fw-medium">${escapeHtml(s.name)}</a></td>
        <td>${statusBadge(s.status)}</td>
        <td class="text-secondary small text-truncate" style="max-width: 200px;">${escapeHtml(s.base_url)}</td>
      </tr>
    `).join('');
    sourcesEl.innerHTML = `
      <table class="table app-table mb-0">
        <thead><tr><th>Name</th><th>Status</th><th>URL</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}
