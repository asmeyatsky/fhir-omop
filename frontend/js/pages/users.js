/**
 * User management (ADMIN) — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { roleBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderUsers(root) {
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">User Management</h1>
        <p class="app-page-subtitle mb-0">Manage platform users and roles</p>
      </div>
      <button type="button" id="add-user-btn" class="btn btn-primary">
        <i class="bi bi-person-plus me-2"></i>Add User
      </button>
    </div>
    <div class="card app-card">
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
        <div class="table-responsive">
          <table class="table app-table mb-0">
            <thead><tr><th>User</th><th>Role</th><th>Tenant</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>
              ${users.map(u => `
                <tr>
                  <td>
                    <div class="d-flex align-items-center gap-3">
                      <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center fw-medium" style="width: 2.25rem; height: 2.25rem; font-size: 0.9rem;">${escapeHtml((u.email || '?')[0].toUpperCase())}</div>
                      <div>
                        <div class="fw-medium">${escapeHtml(u.full_name)}</div>
                        <div class="small text-secondary">${escapeHtml(u.email)}</div>
                      </div>
                    </div>
                  </td>
                  <td>${roleBadge(u.role)}</td>
                  <td class="small text-secondary font-monospace">${u.tenant_id.substring(0, 8)}…</td>
                  <td>${u.is_active ? '<span class="badge badge-app-success">Active</span>' : '<span class="badge badge-app-danger">Inactive</span>'}</td>
                  <td class="text-secondary small">${formatDateTime(u.created_at)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
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
      <h5 class="mb-4">Create User</h5>
      <form id="user-form">
        <div class="mb-3">
          <label class="form-label">Full Name</label>
          <input type="text" name="full_name" class="form-control" placeholder="Dr. Mohammed Al-Rashid" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Email Address</label>
          <input type="email" name="email" class="form-control" placeholder="m.alrashid@hospital.sa" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" name="password" class="form-control" placeholder="Minimum 8 characters" required minlength="8">
        </div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Role</label>
            <select name="role" class="form-select" required>
              <option value="operator">Operator</option>
              <option value="data_steward">Data Steward</option>
              <option value="auditor">Auditor</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">Tenant</label>
            <select name="tenant_id" class="form-select" required>${tenantOpts || '<option disabled>No tenants</option>'}</select>
          </div>
        </div>
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Create User</button>
        </div>
      </form>
    `);
    document.getElementById('user-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await api.post('/api/v1/users', Object.fromEntries(new FormData(e.target)));
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
