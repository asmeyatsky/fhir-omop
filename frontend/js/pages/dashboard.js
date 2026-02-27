/**
 * Dashboard page with KPI cards, recent activity, and system health.
 */
import { api } from '../core/api.js';
import { currentUser } from '../core/auth.js';
import { formatNumber, statusBadge, timeAgo, loadingCards, toast } from '../core/utils.js';

export async function renderDashboard(root) {
  const user = currentUser();
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Welcome back, ${user?.email || 'User'}</p>
      </div>
      <div class="flex items-center gap-2">
        <span id="health-indicator" class="badge badge-neutral">checking...</span>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8" id="kpi-grid">
      ${loadingCards(4)}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Pipelines -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-sm font-semibold text-white">Recent Pipelines</h3>
          <a href="#/pipelines" class="text-xs text-teal-400 hover:text-teal-300">View all</a>
        </div>
        <div class="card-body p-0" id="recent-pipelines"></div>
      </div>

      <!-- Recent Sources -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-sm font-semibold text-white">FHIR Source Connections</h3>
          <a href="#/sources" class="text-xs text-teal-400 hover:text-teal-300">View all</a>
        </div>
        <div class="card-body p-0" id="recent-sources"></div>
      </div>
    </div>
  `;

  // Load data in parallel
  const [healthRes, sourcesRes, pipelinesRes] = await Promise.allSettled([
    fetch('/health').then(r => r.json()),
    api.get('/api/v1/sources').catch(() => []),
    api.get('/api/v1/pipelines').catch(() => []),
  ]);

  const health = healthRes.status === 'fulfilled' ? healthRes.value : null;
  const sources = sourcesRes.status === 'fulfilled' ? sourcesRes.value : [];
  const pipelines = pipelinesRes.status === 'fulfilled' ? pipelinesRes.value : [];

  // Health indicator
  const hi = document.getElementById('health-indicator');
  if (health?.status === 'healthy') {
    hi.className = 'badge badge-success';
    hi.textContent = 'System Healthy';
  } else {
    hi.className = 'badge badge-error';
    hi.textContent = 'System Degraded';
  }

  // KPI cards
  const completedPipelines = pipelines.filter(p => p.status === 'completed').length;
  const totalRecords = pipelines.reduce((sum, p) => sum + (p.total_records || 0), 0);
  const totalErrors = pipelines.reduce((sum, p) => sum + (p.total_errors || 0), 0);

  document.getElementById('kpi-grid').innerHTML = `
    <div class="kpi-card">
      <div class="kpi-icon bg-teal-500/15">
        <svg class="w-5 h-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2"/></svg>
      </div>
      <div class="kpi-value">${formatNumber(sources.length)}</div>
      <div class="kpi-label">FHIR Sources</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon bg-blue-500/15">
        <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
      </div>
      <div class="kpi-value">${formatNumber(pipelines.length)}</div>
      <div class="kpi-label">Total Pipelines</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon bg-emerald-500/15">
        <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      </div>
      <div class="kpi-value">${formatNumber(completedPipelines)}</div>
      <div class="kpi-label">Completed Runs</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon bg-gold-500/15">
        <svg class="w-5 h-5 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"/></svg>
      </div>
      <div class="kpi-value">${formatNumber(totalRecords)}</div>
      <div class="kpi-label">Records Transformed</div>
    </div>
  `;

  // Recent pipelines table
  const pipelinesEl = document.getElementById('recent-pipelines');
  if (pipelines.length === 0) {
    pipelinesEl.innerHTML = '<div class="empty-state py-8"><p class="text-gray-500 text-sm">No pipelines yet</p></div>';
  } else {
    const rows = pipelines.slice(0, 5).map(p => `
      <tr class="cursor-pointer" onclick="window.location.hash='#/pipelines'">
        <td class="font-medium text-gray-200">${p.name}</td>
        <td>${statusBadge(p.status)}</td>
        <td class="text-gray-400">${formatNumber(p.total_records)}</td>
        <td class="text-gray-400">${timeAgo(p.created_at)}</td>
      </tr>
    `).join('');
    pipelinesEl.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Name</th><th>Status</th><th>Records</th><th>Created</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  // Recent sources table
  const sourcesEl = document.getElementById('recent-sources');
  if (sources.length === 0) {
    sourcesEl.innerHTML = '<div class="empty-state py-8"><p class="text-gray-500 text-sm">No sources configured</p></div>';
  } else {
    const rows = sources.slice(0, 5).map(s => `
      <tr class="cursor-pointer" onclick="window.location.hash='#/sources'">
        <td class="font-medium text-gray-200">${s.name}</td>
        <td>${statusBadge(s.status)}</td>
        <td class="text-gray-400 text-xs font-mono truncate max-w-[200px]">${s.base_url}</td>
      </tr>
    `).join('');
    sourcesEl.innerHTML = `
      <table class="data-table">
        <thead><tr><th>Name</th><th>Status</th><th>URL</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }
}
