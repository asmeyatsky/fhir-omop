/**
 * Application bootstrap: register routes, init nav, start router.
 */
import { registerRoute, startRouter } from './core/router.js';
import { currentUser, clearTokens, hasRole, isAuthenticated } from './core/auth.js';
import { roleBadge } from './core/utils.js';

// Page modules
import { renderLogin } from './pages/login.js';
import { renderDashboard } from './pages/dashboard.js';
import { renderSources } from './pages/sources.js';
import { renderMappings } from './pages/mappings.js';
import { renderPipelines } from './pages/pipelines.js';
import { renderUsers } from './pages/users.js';
import { renderAudit } from './pages/audit.js';
import { renderConsent } from './pages/consent.js';
import { renderTenants } from './pages/tenants.js';

// Register all routes
registerRoute('#/login',     { render: renderLogin });
registerRoute('#/dashboard', { render: renderDashboard });
registerRoute('#/sources',   { render: renderSources });
registerRoute('#/mappings',  { render: renderMappings });
registerRoute('#/pipelines', { render: renderPipelines });
registerRoute('#/users',     { render: renderUsers, roles: ['admin'] });
registerRoute('#/audit',     { render: renderAudit, roles: ['admin', 'auditor'] });
registerRoute('#/consent',   { render: renderConsent });
registerRoute('#/tenants',   { render: renderTenants, roles: ['admin'] });

// Update user info in sidebar
function updateSidebar() {
  const user = currentUser();
  if (!user) return;

  const avatar = document.getElementById('user-avatar');
  const email = document.getElementById('user-email');
  const badge = document.getElementById('user-role-badge');

  if (avatar) avatar.textContent = (user.email || '?')[0].toUpperCase();
  if (email) email.textContent = user.email;
  if (badge) badge.innerHTML = roleBadge(user.role);

  // Role-based nav visibility
  document.querySelectorAll('.admin-only').forEach(el => {
    el.classList.toggle('hidden', !hasRole('admin'));
  });
  document.querySelectorAll('.audit-visible').forEach(el => {
    el.classList.toggle('hidden', !hasRole('admin', 'auditor'));
  });
  const adminLabel = document.getElementById('admin-section-label');
  if (adminLabel) {
    adminLabel.classList.toggle('hidden', !hasRole('admin', 'auditor'));
  }
}

// Logout handler
document.getElementById('logout-btn')?.addEventListener('click', () => {
  clearTokens();
  window.location.hash = '#/login';
});

// Listen for auth changes to update sidebar
window.addEventListener('hashchange', () => {
  if (isAuthenticated()) updateSidebar();
});

// Boot
if (!window.location.hash) window.location.hash = '#/dashboard';
updateSidebar();
startRouter();
