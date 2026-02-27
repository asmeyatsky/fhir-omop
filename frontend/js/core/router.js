/**
 * Hash-based SPA router with auth guards.
 */
import { isAuthenticated, hasRole } from './auth.js';

const routes = [];
let currentCleanup = null;

export function registerRoute(hash, { render, guard = null, roles = null }) {
  routes.push({ hash, render, guard, roles });
}

export function navigate(hash) {
  window.location.hash = hash;
}

export async function handleRoute() {
  const hash = window.location.hash || '#/dashboard';
  const path = hash.split('?')[0];

  // Find matching route
  let route = routes.find(r => r.hash === path);
  if (!route) route = routes.find(r => r.hash === '#/dashboard');

  // Auth guard
  if (route && route.hash !== '#/login' && !isAuthenticated()) {
    window.location.hash = '#/login';
    return;
  }

  // Already logged in, redirect from login
  if (route && route.hash === '#/login' && isAuthenticated()) {
    window.location.hash = '#/dashboard';
    return;
  }

  // Role guard
  if (route && route.roles && !hasRole(...route.roles)) {
    window.location.hash = '#/dashboard';
    return;
  }

  if (!route) return;

  // Cleanup previous page
  if (currentCleanup && typeof currentCleanup === 'function') {
    currentCleanup();
    currentCleanup = null;
  }

  // Determine render target
  const isLogin = route.hash === '#/login';
  const loginRoot = document.getElementById('login-root');
  const appShell = document.getElementById('app-shell');
  const pageContent = document.getElementById('page-content');

  if (isLogin) {
    loginRoot.classList.remove('d-none');
    appShell.classList.add('d-none');
    currentCleanup = await route.render(loginRoot);
  } else {
    loginRoot.classList.add('d-none');
    appShell.classList.remove('d-none');
    appShell.classList.add('d-flex');
    currentCleanup = await route.render(pageContent);
  }

  document.querySelectorAll('.nav-link-app[href], .dropdown-item[href]').forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === path);
  });
}

export function startRouter() {
  window.addEventListener('hashchange', handleRoute);
  handleRoute();
}
