/**
 * Login page.
 */
import { api } from '../core/api.js';
import { saveTokens, saveUser } from '../core/auth.js';
import { toast } from '../core/utils.js';

export async function renderLogin(root) {
  root.innerHTML = `
    <div class="min-h-screen flex items-center justify-center p-4">
      <div class="w-full max-w-md">
        <!-- Brand -->
        <div class="text-center mb-8">
          <div class="w-14 h-14 bg-gradient-to-br from-teal-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-teal-500/20">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-white">FHIR-to-OMOP Accelerator</h1>
          <p class="text-gray-400 text-sm mt-2">Enterprise Clinical Data Transformation Platform</p>
        </div>

        <!-- Login card -->
        <div class="card">
          <div class="card-body">
            <h2 class="text-lg font-semibold text-white mb-6">Sign in to your account</h2>
            <form id="login-form" class="space-y-4">
              <div>
                <label class="form-label" for="login-email">Email address</label>
                <input type="email" id="login-email" class="form-input" placeholder="admin@hospital.sa" required autocomplete="email">
              </div>
              <div>
                <label class="form-label" for="login-password">Password</label>
                <input type="password" id="login-password" class="form-input" placeholder="Enter your password" required autocomplete="current-password">
              </div>
              <button type="submit" id="login-submit" class="btn btn-primary w-full py-2.5">
                <span id="login-text">Sign in</span>
                <svg id="login-spinner" class="hidden w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              </button>
            </form>
            <p class="text-xs text-gray-500 text-center mt-6">Protected under NCA ECC-2:2024 compliance</p>
          </div>
        </div>

        <p class="text-center text-xs text-gray-600 mt-6">FHIR-to-OMOP Data Accelerator v0.2.0</p>
      </div>
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
    spinner.classList.remove('hidden');
    btnText.textContent = 'Signing in...';

    try {
      const tokens = await api.post('/api/v1/auth/login', { email, password });
      saveTokens(tokens.access_token, tokens.refresh_token);

      // Fetch user info
      const user = await api.get('/api/v1/auth/me');
      saveUser(user);

      toast('Welcome back!', 'success');
      window.location.hash = '#/dashboard';
    } catch (err) {
      toast(err.message || 'Invalid credentials', 'error');
    } finally {
      submitBtn.disabled = false;
      spinner.classList.add('hidden');
      btnText.textContent = 'Sign in';
    }
  });
}
