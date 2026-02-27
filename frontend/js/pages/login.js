/**
 * Login page — Bootstrap 5 sign-in template (light background, single centered form).
 * No dark panels; all text is dark on light for guaranteed visibility.
 */
import { api } from '../core/api.js';
import { saveTokens, saveUser } from '../core/auth.js';
import { toast } from '../core/utils.js';

export async function renderLogin(root) {
  root.innerHTML = `
    <div class="sign-in-wrapper text-center">
      <main class="form-signin w-100 m-auto">
        <form id="login-form">
          <div class="mb-4">
            <i class="bi bi-database-gear text-primary" style="font-size: 3rem;"></i>
            <h1 class="h3 mb-2 fw-normal">Please sign in</h1>
            <p class="text-body-secondary small">FHIR-to-OMOP Data Accelerator</p>
          </div>
          <div class="form-floating mb-3">
            <input type="email" class="form-control" id="login-email" placeholder="name@example.com" required autocomplete="email">
            <label for="login-email">Email address</label>
          </div>
          <div class="form-floating mb-3">
            <input type="password" class="form-control" id="login-password" placeholder="Password" required autocomplete="current-password">
            <label for="login-password">Password</label>
          </div>
          <button class="btn btn-primary w-100 py-2 mb-3" type="submit" id="login-submit">
            <span id="login-text">Sign in</span>
            <span id="login-spinner" class="spinner-border spinner-border-sm ms-2 d-none" role="status"></span>
          </button>
          <p class="mt-4 mb-0 text-body-secondary small">&copy; FHIR-to-OMOP · NCA ECC-2:2024</p>
        </form>
      </main>
    </div>
  `;

  const form = root.querySelector('#login-form');
  const submitBtn = root.querySelector('#login-submit');
  const spinner = root.querySelector('#login-spinner');
  const btnText = root.querySelector('#login-text');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = root.querySelector('#login-email').value;
    const password = root.querySelector('#login-password').value;

    submitBtn.disabled = true;
    spinner.classList.remove('d-none');
    btnText.textContent = 'Signing in…';

    try {
      const tokens = await api.post('/api/v1/auth/login', { email, password });
      saveTokens(tokens.access_token, tokens.refresh_token);
      const user = await api.get('/api/v1/auth/me');
      saveUser(user);
      toast('Welcome back!', 'success');
      window.location.hash = '#/dashboard';
    } catch (err) {
      toast(err.message || 'Invalid credentials', 'error');
    } finally {
      submitBtn.disabled = false;
      spinner.classList.add('d-none');
      btnText.textContent = 'Sign in';
    }
  });
}
