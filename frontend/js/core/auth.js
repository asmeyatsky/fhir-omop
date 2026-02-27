/**
 * Authentication token management.
 */

const ACCESS_KEY = 'fhir_omop_access_token';
const REFRESH_KEY = 'fhir_omop_refresh_token';
const USER_KEY = 'fhir_omop_user';

export function saveTokens(access, refresh) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function getToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isAuthenticated() {
  const token = getToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function hasRole(...roles) {
  const user = currentUser();
  return user && roles.includes(user.role);
}

export function hasPermission(perm) {
  const user = currentUser();
  return user && user.permissions && user.permissions.includes(perm);
}
