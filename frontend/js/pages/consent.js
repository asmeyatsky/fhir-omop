/**
 * Patient consent management page (PDPL compliance).
 */
import { api } from '../core/api.js';
import { statusBadge, formatDateTime, toast, showModal, closeModal, emptyState, escapeHtml } from '../core/utils.js';

export async function renderConsent(root) {
  root.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Patient Consent</h1>
        <p class="page-subtitle">PDPL-compliant consent management</p>
      </div>
      <button id="grant-consent-btn" class="btn btn-primary">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
        Grant Consent
      </button>
    </div>

    <!-- Search -->
    <div class="card mb-6">
      <div class="card-body">
        <div class="flex gap-4 items-end">
          <div class="flex-1">
            <label class="form-label">Filter by Patient ID</label>
            <input type="text" id="consent-patient-filter" class="form-input" placeholder="Patient identifier">
          </div>
          <button id="consent-search" class="btn btn-primary btn-sm">Search</button>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body p-0" id="consent-table"></div>
    </div>
  `;

  async function loadConsents(patientId = null) {
    try {
      const query = {};
      if (patientId) query.patient_id = patientId;
      const data = await api.get('/api/v1/consent', query);
      const consents = data.consents || [];
      const el = document.getElementById('consent-table');

      if (!consents.length) {
        el.innerHTML = emptyState('No consent records found');
        return;
      }

      el.innerHTML = `
        <table class="data-table">
          <thead><tr><th>Patient ID</th><th>Purpose</th><th>Scope</th><th>Status</th><th>Granted</th><th>Expires</th><th>Actions</th></tr></thead>
          <tbody>
            ${consents.map(c => `
              <tr>
                <td class="font-mono text-xs text-gray-300">${escapeHtml(c.patient_id)}</td>
                <td><span class="badge badge-info">${c.purpose}</span></td>
                <td class="text-gray-400 text-xs">${c.scope}</td>
                <td>${statusBadge(c.status)}</td>
                <td class="text-gray-400 text-xs">${formatDateTime(c.granted_at)}</td>
                <td class="text-gray-400 text-xs">${formatDateTime(c.expires_at)}</td>
                <td>
                  ${c.status === 'granted' && c.is_valid ? `
                    <button class="btn btn-danger btn-sm revoke-btn" data-id="${c.id}">Revoke</button>
                  ` : '<span class="text-xs text-gray-600">—</span>'}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;

      el.querySelectorAll('.revoke-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          if (!confirm('Are you sure you want to revoke this consent?')) return;
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

  // Search handler
  document.getElementById('consent-search').addEventListener('click', () => {
    const pid = document.getElementById('consent-patient-filter').value.trim();
    loadConsents(pid || null);
  });

  // Grant consent modal
  document.getElementById('grant-consent-btn').addEventListener('click', () => {
    showModal(`
      <div class="p-6">
        <h3 class="text-lg font-semibold text-white mb-4">Grant Patient Consent</h3>
        <form id="consent-form" class="space-y-4">
          <div>
            <label class="form-label">Patient ID</label>
            <input type="text" name="patient_id" class="form-input" placeholder="Patient identifier" required>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Purpose</label>
              <select name="purpose" class="form-select" required>
                <option value="treatment">Treatment</option>
                <option value="research">Research</option>
                <option value="operations">Operations</option>
                <option value="marketing">Marketing</option>
              </select>
            </div>
            <div>
              <label class="form-label">Scope</label>
              <select name="scope" class="form-select" required>
                <option value="full_record">Full Record</option>
                <option value="specific_resources">Specific Resources</option>
                <option value="anonymized">Anonymized</option>
              </select>
            </div>
          </div>
          <div>
            <label class="form-label">Expiration Date (optional)</label>
            <input type="datetime-local" name="expires_at" class="form-input">
          </div>
          <div>
            <label class="form-label">Notes (optional)</label>
            <textarea name="notes" class="form-input" rows="2" placeholder="Consent details..."></textarea>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="btn btn-secondary" onclick="document.getElementById('modal-backdrop').classList.add('hidden')">Cancel</button>
            <button type="submit" class="btn btn-primary">Grant Consent</button>
          </div>
        </form>
      </div>
    `);

    document.getElementById('consent-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const data = {
        patient_id: fd.get('patient_id'),
        purpose: fd.get('purpose'),
        scope: fd.get('scope'),
      };
      if (fd.get('expires_at')) data.expires_at = new Date(fd.get('expires_at')).toISOString();
      if (fd.get('notes')) data.notes = fd.get('notes');

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
