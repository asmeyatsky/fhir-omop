/**
 * Tenants (ADMIN) — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderTenants(root) {
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">Tenants</h1>
        <p class="app-page-subtitle mb-0">Hospital and organization management</p>
      </div>
      <button type="button" id="add-tenant-btn" class="btn btn-primary">
        <i class="bi bi-plus-lg me-2"></i>Add Tenant
      </button>
    </div>
    <div class="row g-4" id="tenants-grid"></div>
  `;

  async function loadTenants() {
    try {
      const tenants = await api.get('/api/v1/tenants');
      const el = document.getElementById('tenants-grid');
      if (!tenants.length) {
        el.innerHTML = `<div class="col-12">${emptyState('No tenants configured')}</div>`;
        return;
      }
      el.innerHTML = tenants.map(t => `
        <div class="col-12 col-md-6 col-lg-4">
          <div class="card app-card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start mb-3">
                <div>
                  <h6 class="mb-1 fw-semibold">${escapeHtml(t.name)}</h6>
                  <p class="small text-secondary mb-0">${escapeHtml(t.hospital_name)}</p>
                </div>
                ${t.is_active ? '<span class="badge badge-app-success">Active</span>' : '<span class="badge badge-app-danger">Inactive</span>'}
              </div>
              <div class="small">
                ${t.nphies_facility_id ? `<div class="d-flex justify-content-between mb-1"><span class="text-secondary">NPHIES Facility ID</span><code>${escapeHtml(t.nphies_facility_id)}</code></div>` : ''}
                <div class="d-flex justify-content-between mb-1"><span class="text-secondary">Tenant ID</span><code>${t.id.substring(0, 12)}…</code></div>
                <div class="d-flex justify-content-between"><span class="text-secondary">Created</span>${formatDateTime(t.created_at)}</div>
              </div>
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
      <h5 class="mb-4">Add Tenant</h5>
      <form id="tenant-form">
        <div class="mb-3">
          <label class="form-label">Tenant Name</label>
          <input type="text" name="name" class="form-control" placeholder="e.g. riyadh-central" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Hospital Name</label>
          <input type="text" name="hospital_name" class="form-control" placeholder="e.g. King Faisal Specialist Hospital" required>
        </div>
        <div class="mb-3">
          <label class="form-label">NPHIES Facility ID (optional)</label>
          <input type="text" name="nphies_facility_id" class="form-control" placeholder="e.g. NPHIES-12345">
        </div>
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Create Tenant</button>
        </div>
      </form>
    `);
    document.getElementById('tenant-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(e.target));
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
