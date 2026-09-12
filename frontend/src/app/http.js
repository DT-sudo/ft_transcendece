import { getBootstrap } from './bootstrap.js';

function cookie(name) {
  for (const part of (document.cookie || '').split(';')) {
    const trimmed = part.trim();
    if (trimmed.startsWith(`${name}=`)) {
      return decodeURIComponent(trimmed.slice(name.length + 1));
    }
  }
  return '';
}

export function getCsrfToken() {
  return getBootstrap().csrfToken || cookie('csrftoken');
}

// "/manager/shifts/0/delete/" + 12 -> "/manager/shifts/12/delete/"
export function urlFromTemplate(template, id) {
  const tpl = String(template || '');
  const idStr = String(id ?? '').trim();
  if (tpl && idStr && tpl.includes('/0/')) {
    return tpl.replace('/0/', `/${idStr}/`);
  }
  return tpl;
}

function firstErrorMessage(payload) {
  const errors = payload?.errors;
  if (!errors || typeof errors !== 'object') return '';

  for (const item of Object.values(errors).flat()) {
    if (typeof item === 'string' && item) return item;
    if (item?.message) return item.message;
  }
  return '';
}

export async function postForm(url, data) {
  const headers = {
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    Accept: 'application/json',
  };
  const token = getCsrfToken();
  if (token) headers['X-CSRFToken'] = token;

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: new URLSearchParams(data || {}),
  });

  const payload = await response.json().catch(() => ({}));
  if (response.ok) return payload;

  throw new Error(payload.error || firstErrorMessage(payload) || 'Request failed.');
}

/**
 * Build a "?a=1&a=2&b=3" query string from a flat { key: value | value[] }
 * object, dropping empty/undefined entries. Shared by the search and
 * analytics filter bars, whose filter shape (arrays for multiselects,
 * strings for everything else) is otherwise identical.
 */
export function toQueryString(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value == null || value === '') continue;
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== '' && item != null) search.append(key, item);
      });
    } else {
      search.set(key, value);
    }
  }
  return search.toString();
}

/** GET a JSON endpoint (analytics refresh/polling) using the same CSRF setup as postForm. */
export async function getJSON(url, params) {
  const query = toQueryString(params);
  const response = await fetch(query ? `${url}?${query}` : url, {
    headers: { Accept: 'application/json' },
  });
  const payload = await response.json().catch(() => ({}));
  if (response.ok) return payload;
  throw new Error(payload.error || 'Request failed.');
}
