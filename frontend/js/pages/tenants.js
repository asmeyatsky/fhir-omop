/**
 * Hospital tenant management page (ADMIN only).
 */
import { api } from '../core/api.js';
import { formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderTenants(root) {
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Tenants</h1>
        <p class="page-subtitle">Hospital and organization management</p>
      </div>
      <button id="add-tenant-btn" class="btn btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        Add Tenant
      </button>
    </div>
    <div id="tenants-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
  `;

  async function loadTenants() {
    try {
      const tenants = await api.get('/api/v1/tenants');
      const el = document.getElementById('tenants-grid');

      if (!tenants.length) {
        el.innerHTML = `<div class="col-span-3">${emptyState('No tenants configured')}</div>`;
        return;
      }

      el.innerHTML = tenants.map(t => `
        <div class="card p-5 hover:border-teal-500/30 transition-colors">
          <div class="flex items-start justify-between mb-3">
            <div>
              <h3 class="text-sm font-semibold text-white">${escapeHtml(t.name)}</h3>
              <p class="text-xs text-gray-400 mt-0.5">${escapeHtml(t.hospital_name)}</p>
            </div>
            ${t.is_active
              ? '<span class="badge badge-success">Active</span>'
              : '<span class="badge badge-error">Inactive</span>'}
          </div>
          <div class="space-y-2 text-xs">
            ${t.nphies_facility_id ? `
              <div class="flex justify-between">
                <span class="text-gray-500">NPHIES Facility ID</span>
                <span class="font-mono text-gray-300">${escapeHtml(t.nphies_facility_id)}</span>
              </div>
            ` : ''}
            <div class="flex justify-between">
              <span class="text-gray-500">Tenant ID</span>
              <span class="font-mono text-gray-400">${t.id.substring(0, 12)}...</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Created</span>
              <span class="text-gray-400">${formatDateTime(t.created_at)}</span>
            </div>
          </div>
        </div>
      `).join('');
    } catch (err) {
      toast('Failed to load tenants', 'error');
    }
  }

  document.getElementById('add-tenant-btn').addEventListener('click', () => {
    showModal(`
      <div class="p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Add Tenant</h3>
        <form id="tenant-form" class="space-y-4">
          <div>
            <label class="form-label">Tenant Name</label>
            <input type="text" name="name" class="form-input" placeholder="e.g., riyadh-central" required>
          </div>
          <div>
            <label class="form-label">Hospital Name</label>
            <input type="text" name="hospital_name" class="form-input" placeholder="e.g., King Faisal Specialist Hospital" required>
          </div>
          <div>
            <label class="form-label">NPHIES Facility ID (optional)</label>
            <input type="text" name="nphies_facility_id" class="form-input" placeholder="e.g., NPHIES-12345">
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Create Tenant</button>
          </div>
        </form>
      </div>
    `);

    document.getElementById('tenant-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const data = Object.fromEntries(fd);
      if (!data.nphies_facility_id) delete data.nphies_facility_id;
      try {
        await api.post('/api/v1/tenants', data);
        closeModal();
        toast('Tenant created successfully', 'success');
        loadTenants();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  loadTenants();
}
