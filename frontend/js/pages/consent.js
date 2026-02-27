/**
 * Consent (PDPL) — Bootstrap 5.
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderConsent(root) {
  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">Patient Consent</h1>
        <p class="app-page-subtitle mb-0">PDPL-compliant consent management</p>
      </div>
      <button type="button" id="grant-consent-btn" class="btn btn-primary">
        <i class="bi bi-shield-plus me-2"></i>Grant Consent
      </button>
    </div>
    <div class="card app-card mb-4">
      <div class="card-body">
        <div class="row g-3 align-items-end">
          <div class="col-12 col-md-8">
            <label class="form-label">Filter by Patient ID</label>
            <input type="text" id="consent-patient-filter" class="form-control" placeholder="Patient identifier">
          </div>
          <div class="col-12 col-md-4">
            <button type="button" id="consent-search" class="btn btn-primary w-100">Search</button>
          </div>
        </div>
      </div>
    </div>
    <div class="card app-card">
      <div class="card-body p-0" id="consent-table"></div>
    </div>
  `;

  async function loadConsents(patientId = null) {
    try {
      const query = patientId ? { patient_id: patientId } : {};
      const data = await api.get('/api/v1/consent', query);
      const consents = data.consents || [];
      const el = document.getElementById('consent-table');
      if (!consents.length) {
        el.innerHTML = emptyState('No consent records found');
        return;
      }
      el.innerHTML = `
        <div class="table-responsive">
          <table class="table app-table mb-0">
            <thead><tr><th>Patient ID</th><th>Purpose</th><th>Scope</th><th>Status</th><th>Granted</th><th>Expires</th><th></th></tr></thead>
            <tbody>
              ${consents.map(c => `
                <tr>
                  <td class="small font-monospace">${escapeHtml(c.patient_id)}</td>
                  <td><span class="badge badge-app-info">${escapeHtml(c.purpose)}</span></td>
                  <td class="small text-secondary">${escapeHtml(c.scope)}</td>
                  <td>${statusBadge(c.status)}</td>
                  <td class="small text-secondary">${formatDateTime(c.granted_at)}</td>
                  <td class="small text-secondary">${formatDateTime(c.expires_at)}</td>
                  <td>
                    ${c.status === 'granted' && c.is_valid ? `<button type="button" class="btn btn-sm btn-outline-danger revoke-btn" data-id="${escapeHtml(c.id)}">Revoke</button>` : '<span class="text-muted small">—</span>'}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      el.querySelectorAll('.revoke-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          if (!confirm('Revoke this consent?')) return;
          try {
            await api.post(`/api/v1/consent/${btn.dataset.id}/revoke`);
            toast('Consent revoked', 'success');
            loadConsents(patientId);
          } catch (err) {
            toast(err.message, 'error');
          }
        });
      });
    } catch (err) {
      toast('Failed to load consents', 'error');
    }
  }

  document.getElementById('consent-search').addEventListener('click', () => {
    loadConsents(document.getElementById('consent-patient-filter').value.trim() || null);
  });

  document.getElementById('grant-consent-btn').addEventListener('click', () => {
    showModal(`
      <h5 class="mb-4">Grant Patient Consent</h5>
      <form id="consent-form">
        <div class="mb-3">
          <label class="form-label">Patient ID</label>
          <input type="text" name="patient_id" class="form-control" placeholder="Patient identifier" required>
        </div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Purpose</label>
            <select name="purpose" class="form-select" required>
              <option value="treatment">Treatment</option>
              <option value="research">Research</option>
              <option value="billing">Billing</option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">Scope</label>
            <input type="text" name="scope" class="form-control" placeholder="e.g. full record" required>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label">Expires at (optional)</label>
          <input type="datetime-local" name="expires_at" class="form-control">
        </div>
        <div class="d-flex justify-content-end gap-2 mt-4">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Grant Consent</button>
        </div>
      </form>
    `);
    document.getElementById('consent-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const data = Object.fromEntries(fd);
      if (!data.expires_at) delete data.expires_at;
      try {
        await api.post('/api/v1/consent', data);
        closeModal();
        toast('Consent granted', 'success');
        loadConsents();
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  });

  loadConsents();
}
