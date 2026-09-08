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
