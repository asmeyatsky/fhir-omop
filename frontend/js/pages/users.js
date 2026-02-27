/**
 * User management page (ADMIN only).
 */
import { api } from '../core/api.js';
import { roleBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderUsers(root) {
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">User Management</h1>
        <p class="page-subtitle">Manage platform users and their roles</p>
      </div>
      <button id="add-user-btn" class="btn btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/></svg>
        Add User
      </button>
    </div>
    <div class="card">
      <div class="card-body p-0" id="users-table"></div>
    </div>
  `;

  async function loadUsers() {
    try {
      const users = await api.get('/api/v1/users');
      const el = document.getElementById('users-table');
      if (!users.length) {
        el.innerHTML = emptyState('No users found');
        return;
      }
      el.innerHTML = `
        <table class="data-table">
          <thead><tr><th>User</th><th>Role</th><th>Tenant</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>
            ${users.map(u => `
              <tr>
                <td>
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-brand-400 rounded-full flex items-center justify-center text-sm font-medium text-white">${(u.email || '?')[0].toUpperCase()}</div>
                    <div>
                      <div class="font-medium text-ink-800">${escapeHtml(u.full_name)}</div>
                      <div class="text-xs text-ink-500">${escapeHtml(u.email)}</div>
                    </div>
                  </div>
                </td>
                <td>${roleBadge(u.role)}</td>
                <td class="text-xs text-ink-500 font-mono">${u.tenant_id.substring(0, 8)}...</td>
                <td>${u.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-error">Inactive</span>'}</td>
                <td class="text-ink-500 text-xs">${formatDateTime(u.created_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (err) {
      toast('Failed to load users', 'error');
    }
  }

  document.getElementById('add-user-btn').addEventListener('click', async () => {
    let tenants = [];
    try { tenants = await api.get('/api/v1/tenants'); } catch {}

    const tenantOpts = tenants.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');

    showModal(`
      <div class="p-6">
        <h3 class="text-lg font-semibold text-ink-900 mb-4">Create User</h3>
        <form id="user-form" class="space-y-4">
          <div>
            <label class="form-label">Full Name</label>
            <input type="text" name="full_name" class="form-input" placeholder="Dr. Mohammed Al-Rashid" required>
          </div>
          <div>
            <label class="form-label">Email Address</label>
            <input type="email" name="email" class="form-input" placeholder="m.alrashid@hospital.sa" required>
          </div>
          <div>
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-input" placeholder="Minimum 8 characters" required minlength="8">
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Role</label>
              <select name="role" class="form-select" required>
                <option value="operator">Operator</option>
                <option value="data_steward">Data Steward</option>
                <option value="auditor">Auditor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label class="form-label">Tenant</label>
              <select name="tenant_id" class="form-select" required>${tenantOpts || '<option disabled>No tenants</option>'}</select>
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Create User</button>
          </div>
        </form>
      </div>
    `);

    document.getElementById('user-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api.post('/api/v1/users', Object.fromEntries(fd));
        closeModal();
        toast('User created successfully', 'success');
        loadUsers();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  loadUsers();
}
