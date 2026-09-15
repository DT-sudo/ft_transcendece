// The browser half of i18n. Every string a React page shows comes from the catalogs in
// ./locales; text that is written on the server (flash messages, form errors, the legal
// pages, notifications) is translated by Django, in the same language.
import { cloneElement, isValidElement, useSyncExternalStore } from 'react';

import { getBootstrap, postForm } from '../app/http.js';
import ar from './locales/ar.json';
import cs from './locales/cs.json';
import en from './locales/en.json';

const CATALOGS = { en, cs, ar };
const FALLBACK = 'en';

// Django renders <html lang dir> for the language it picked, so the first paint already matches.
let language = CATALOGS[document.documentElement.lang] ? document.documentElement.lang : FALLBACK;
const listeners = new Set();

export const getLanguage = () => language;

export const isRtl = () => document.documentElement.dir === 'rtl';

/** For `Intl` formatters. Arabic keeps Western digits, like the times and numbers typed into the forms. */
export const intlLocale = () => (language === 'ar' ? 'ar-u-nu-latn' : language);

// 0 = Sunday: Czech weeks start on Monday and Arabic ones on Saturday.
const FIRST_DAY_OF_WEEK = { en: 0, cs: 1, ar: 6 };
export const firstDayOfWeek = () => FIRST_DAY_OF_WEEK[language];

const lookup = (catalog, key) => key.split('.').reduce((node, part) => node?.[part], catalog);

function template(key, count) {
  let entry = lookup(CATALOGS[language], key) ?? lookup(CATALOGS[FALLBACK], key);
  // Plural entries hold one string per CLDR category: `one`/`other` in English, plus `few`/`many`
  // in Czech and `zero`/`two`/`few`/`many` in Arabic.
  if (entry && typeof entry === 'object' && count !== undefined) {
    entry = entry[new Intl.PluralRules(language).select(count)] ?? entry.other;
  }
  return typeof entry === 'string' ? entry : key;
}

/** `t('friends.online', { online: 2, total: 5 })`; a `count` param also picks the plural form. */
export function t(key, params = {}) {
  return template(key, params.count).replace(/\{(\w+)\}/g, (match, name) => (name in params ? String(params[name]) : match));
}

/** Like `t`, but a param may be a React element, for a link inside a sentence. Returns children for JSX. */
export function tx(key, params = {}) {
  return template(key, params.count)
    .split(/(\{\w+\})/)
    .map((part, index) => {
      const name = part.match(/^\{(\w+)\}$/)?.[1];
      if (!name || !(name in params)) return part;
      return isValidElement(params[name]) ? cloneElement(params[name], { key: index }) : String(params[name]);
    });
}

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The current language; a component using it re-renders when the language changes. */
export function useLanguage() {
  return useSyncExternalStore(subscribe, getLanguage);
}

/** Run `callback` after every language change (for state copied from the page data). */
export function onLanguageChange(callback) {
  return subscribe(callback);
}

/** The page's data re-read from the server, now written in the new language; null when it can't be. */
async function rereadPage() {
  const url = new URL(window.location.href);
  url.searchParams.set('format', 'json');
  try {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok || !response.headers.get('Content-Type')?.includes('application/json')) return null;
    return { data: await response.json(), title: response.headers.get('X-Page-Title') };
  } catch {
    return null;
  }
}

/**
 * Switch language in place, with no reload: save the choice, re-read the text the server
 * writes for this page, then flip every string and the page direction together.
 */
export async function changeLanguage(code) {
  if (code === language || !CATALOGS[code]) return;
  const bootstrap = getBootstrap();
  const saved = await postForm(bootstrap.urls.language, { language: code });
  const page = await rereadPage();

  if (page) {
    bootstrap.data = page.data;
    if (page.title) document.title = decodeURIComponent(page.title);
  }
  if (saved.user) bootstrap.user = saved.user;
  bootstrap.locale = { language: code, dir: saved.dir };
  language = code;
  document.documentElement.lang = code;
  document.documentElement.dir = saved.dir;
  listeners.forEach((listener) => listener());
}
