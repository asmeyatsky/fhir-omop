/**
 * Shared utilities: formatters, toast, badges, modals (Bootstrap 5).
 */

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

export function formatNumber(n) {
  if (n === null || n === undefined) return '0';
  return n.toLocaleString();
}

const STATUS_MAP = {
  healthy: 'success', active: 'success', completed: 'success', granted: 'success',
  connected: 'success', running: 'info', in_progress: 'info', pending: 'warning',
  untested: 'neutral', draft: 'neutral',
  failed: 'error', error: 'error', revoked: 'error', disconnected: 'error',
};

const BADGE_CLASS = {
  success: 'badge-app-success',
  warning: 'badge-app-warning',
  error: 'badge-app-danger',
  info: 'badge-app-info',
  neutral: 'badge-app-neutral',
};

export function statusBadge(status) {
  if (!status) return '';
  const type = STATUS_MAP[status.toLowerCase()] || 'neutral';
  const label = status.replace(/_/g, ' ');
  return `<span class="badge ${BADGE_CLASS[type]}">${escapeHtml(label)}</span>`;
}

export function roleBadge(role) {
  if (!role) return '';
  const label = role.replace(/_/g, ' ');
  return `<span class="badge bg-primary">${escapeHtml(label)}</span>`;
}

export function toast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `app-toast app-toast-${type} mb-2`;
  const icon = type === 'success' ? 'bi-check-circle-fill' : type === 'error' ? 'bi-exclamation-circle-fill' : 'bi-info-circle-fill';
  el.innerHTML = `<i class="bi ${icon}"></i><span>${escapeHtml(message)}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transition = 'opacity 0.2s';
    setTimeout(() => el.remove(), 200);
  }, 4000);
}

export function showModal(html) {
  const backdrop = document.getElementById('modal-backdrop');
  const content = document.getElementById('modal-content');
  content.innerHTML = `<div class="modal-body">${html}</div>`;
  const modal = bootstrap.Modal.getOrCreateInstance(backdrop);
  backdrop.addEventListener('hidden.bs.modal', () => { content.innerHTML = ''; }, { once: true });
  modal.show();
}

export function closeModal() {
  const backdrop = document.getElementById('modal-backdrop');
  const modal = bootstrap.Modal.getInstance(backdrop);
  if (modal) modal.hide();
  document.getElementById('modal-content').innerHTML = '';
}

export function escapeHtml(str) {
  if (str == null) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

export function emptyState(message) {
  return `
    <div class="text-center py-5">
      <i class="bi bi-inbox text-secondary" style="font-size: 2.5rem;"></i>
      <p class="text-secondary mt-3 mb-0">${escapeHtml(message)}</p>
    </div>
  `;
}

export function loadingCards(count = 4) {
  return Array(count).fill(`
    <div class="app-stat-card">
      <div class="placeholder-glow">
        <span class="placeholder col-4 rounded"></span>
        <span class="placeholder col-6 rounded mt-2 d-block"></span>
        <span class="placeholder col-5 rounded mt-1 d-block"></span>
      </div>
    </div>
  `).join('');
}

export function loadingTable() {
  const rows = Array(5).fill('<tr><td colspan="99"><span class="placeholder col-12"></span></td></tr>').join('');
  return `<table class="table app-table"><tbody>${rows}</tbody></table>`;
}
