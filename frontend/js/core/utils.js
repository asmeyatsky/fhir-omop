/**
 * Shared utilities: formatters, toast, badges, modals.
 */

// --- Date formatting ---
export function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

export function timeAgo(iso) {
  if (!iso) return '—';
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

// --- Number formatting ---
export function formatNumber(n) {
  if (n === null || n === undefined) return '0';
  return n.toLocaleString();
}

// --- Status badges ---
const STATUS_MAP = {
  healthy: 'success', active: 'success', completed: 'success', granted: 'success',
  connected: 'success', running: 'info', in_progress: 'info', pending: 'warning',
  untested: 'neutral', draft: 'neutral',
  failed: 'error', error: 'error', revoked: 'error', disconnected: 'error',
};

export function statusBadge(status) {
  if (!status) return '';
  const type = STATUS_MAP[status.toLowerCase()] || 'neutral';
  const label = status.replace(/_/g, ' ');
  return `<span class="badge badge-${type}">${label}</span>`;
}

export function roleBadge(role) {
  if (!role) return '';
  const colors = {
    admin: 'text-brand-900 bg-brand-100',
    auditor: 'text-ink-700 bg-ink-100',
    operator: 'text-brand-700 bg-brand-100',
    data_steward: 'text-brand-800 bg-brand-200',
  };
  const cls = colors[role] || 'text-ink-500 bg-ink-100';
  return `<span class="badge ${cls}">${role.replace(/_/g, ' ')}</span>`;
}

// --- Toast notifications ---
export function toast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  const icons = {
    success: '<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
    error: '<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
    info: '<svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
  };
  el.innerHTML = `${icons[type] || icons.info}<span class="text-sm">${escapeHtml(message)}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 200); }, 4000);
}

// --- Modal ---
export function showModal(html) {
  const backdrop = document.getElementById('modal-backdrop');
  const content = document.getElementById('modal-content');
  content.innerHTML = html;
  backdrop.classList.remove('hidden');
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closeModal();
  }, { once: true });
}

export function closeModal() {
  document.getElementById('modal-backdrop').classList.add('hidden');
  document.getElementById('modal-content').innerHTML = '';
}

// --- HTML helpers ---
export function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function emptyState(message, icon = null) {
  const svg = icon || '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/></svg>';
  return `<div class="empty-state">${svg}<p>${escapeHtml(message)}</p></div>`;
}

// --- Loading skeleton ---
export function loadingCards(count = 4) {
  return Array(count).fill('<div class="kpi-card"><div class="skeleton h-10 w-10 rounded-lg mb-4"></div><div class="skeleton h-7 w-20 mb-2"></div><div class="skeleton h-4 w-32"></div></div>').join('');
}

export function loadingTable() {
  const rows = Array(5).fill('<tr><td colspan="99" class="px-4 py-3"><div class="skeleton h-4 w-full"></div></td></tr>').join('');
  return `<table class="data-table"><tbody>${rows}</tbody></table>`;
}
