/**
 * Target Records — paginated view of records loaded into the OMOP target.
 */
import { api } from '../core/api.js';
import { escapeHtml, formatNumber, emptyState, toast } from '../core/utils.js';

const PAGE_SIZES = [20, 50, 100];

export async function renderTargetRecords(root) {
  let currentTable = null;
  let currentPage = 0;
  let pageSize = 20;
  let tables = [];
  let total = 0;
  let data = { columns: [], rows: [], total: 0 };

  root.innerHTML = `
    <div class="app-page-header d-flex flex-wrap justify-content-between align-items-start gap-3">
      <div>
        <h1 class="app-page-title">Target Records</h1>
        <p class="app-page-subtitle mb-0">View records loaded into the OMOP target database</p>
      </div>
      <div class="d-flex align-items-center gap-2">
        <label class="form-label mb-0 text-nowrap">Table</label>
        <select id="target-table-select" class="form-select form-select-sm" style="min-width: 200px;">
          <option value="">Select a table…</option>
        </select>
        <label class="form-label mb-0 text-nowrap ms-2">Rows</label>
        <select id="target-page-size" class="form-select form-select-sm" style="width: 80px;">
          ${PAGE_SIZES.map(n => `<option value="${n}" ${n === 20 ? 'selected' : ''}>${n}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="card app-card">
      <div class="card-body p-0" id="target-records-content"></div>
      <div class="card-footer d-flex flex-wrap justify-content-between align-items-center gap-2 py-2 px-3" id="target-records-pagination"></div>
    </div>
  `;

  const contentEl = document.getElementById('target-records-content');
  const paginationEl = document.getElementById('target-records-pagination');
  const tableSelect = document.getElementById('target-table-select');
  const pageSizeSelect = document.getElementById('target-page-size');

  async function loadTables() {
    try {
      tables = await api.get('/api/v1/target-records/tables');
      tableSelect.innerHTML = '<option value="">Select a table…</option>' +
        tables.map(t => `<option value="${escapeHtml(t.name)}">${escapeHtml(t.name)}${t.count != null ? ` (${formatNumber(t.count)})` : ''}</option>`).join('');
    } catch (err) {
      contentEl.innerHTML = emptyState(err.message || 'Target records not available. Set OMOP_TARGET_READ_URL if using in-memory storage.');
      paginationEl.innerHTML = '';
      return;
    }
  }

  async function loadPage() {
    if (!currentTable) {
      contentEl.innerHTML = emptyState('Select an OMOP table to view its records.');
      paginationEl.innerHTML = '';
      return;
    }
    contentEl.innerHTML = '<div class="p-4 text-center"><span class="spinner-border spinner-border-sm me-2"></span>Loading…</div>';
    paginationEl.innerHTML = '';
    try {
      const offset = currentPage * pageSize;
      data = await api.get('/api/v1/target-records', { table: currentTable, limit: pageSize, offset });
      total = data.total;
      renderTable();
      renderPagination();
    } catch (err) {
      contentEl.innerHTML = emptyState(err.message || 'Failed to load records');
      toast(err.message || 'Failed to load records', 'error');
    }
  }

  function renderTable() {
    if (!data.rows.length) {
      contentEl.innerHTML = emptyState(`No rows in ${escapeHtml(currentTable)}.`);
      return;
    }
    contentEl.innerHTML = `
      <div class="table-responsive">
        <table class="table app-table mb-0">
          <thead>
            <tr>${data.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>
          </thead>
          <tbody>
            ${data.rows.map(row => `
              <tr>${data.columns.map(col => {
                const v = row[col];
                const disp = v == null ? '—' : (typeof v === 'object' ? JSON.stringify(v) : String(v));
                return `<td class="text-break" style="max-width: 200px;">${escapeHtml(disp)}</td>`;
              }).join('')}</tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderPagination() {
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    const start = total === 0 ? 0 : currentPage * pageSize + 1;
    const end = total === 0 ? 0 : Math.min((currentPage + 1) * pageSize, total);
    paginationEl.innerHTML = `
      <div class="small text-secondary">
        Showing ${formatNumber(start)}–${formatNumber(end)} of ${formatNumber(total)} rows
      </div>
      <nav>
        <ul class="pagination pagination-sm mb-0">
          <li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="prev" aria-label="Previous">Previous</a>
          </li>
          <li class="page-item disabled">
            <span class="page-link">Page ${currentPage + 1} of ${totalPages}</span>
          </li>
          <li class="page-item ${currentPage >= totalPages - 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="next" aria-label="Next">Next</a>
          </li>
        </ul>
      </nav>
    `;
    paginationEl.querySelectorAll('[data-page]').forEach(a => {
      a.addEventListener('click', (e) => {
        e.preventDefault();
        if (a.classList.contains('disabled')) return;
        if (a.dataset.page === 'prev' && currentPage > 0) {
          currentPage--;
          loadPage();
        } else if (a.dataset.page === 'next' && currentPage < totalPages - 1) {
          currentPage++;
          loadPage();
        }
      });
    });
  }

  tableSelect.addEventListener('change', () => {
    currentTable = tableSelect.value || null;
    currentPage = 0;
    if (currentTable) loadPage();
    else {
      contentEl.innerHTML = emptyState('Select an OMOP table to view its records.');
      paginationEl.innerHTML = '';
    }
  });

  pageSizeSelect.addEventListener('change', () => {
    pageSize = parseInt(pageSizeSelect.value, 10);
    currentPage = 0;
    if (currentTable) loadPage();
  });

  await loadTables();
  if (!currentTable) {
    contentEl.innerHTML = emptyState('Select an OMOP table to view its records.');
  }
}
