// `npm run i18n:check`: every catalog has the same keys and placeholders as English, and every
// literal key used in the source exists. Plural entries may use different CLDR categories per language.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

// fileURLToPath, not `.pathname`: the project path may contain spaces.
const LOCALES = fileURLToPath(new URL('../src/i18n/locales/', import.meta.url));
const SOURCE = fileURLToPath(new URL('../src/', import.meta.url));
const PLURAL_CATEGORIES = new Set(['zero', 'one', 'two', 'few', 'many', 'other']);

const load = (code) => JSON.parse(readFileSync(join(LOCALES, `${code}.json`), 'utf8'));
const isPlural = (node) => node && typeof node === 'object' && Object.keys(node).every((key) => PLURAL_CATEGORIES.has(key));
const placeholders = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort().join(',');

/** key -> placeholder signature ("name,total"); a plural entry must carry `other`. */
function flatten(node, prefix = '', out = new Map(), problems = []) {
  for (const [key, value] of Object.entries(node)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') out.set(path, placeholders(value));
    else if (isPlural(value)) {
      if (!value.other) problems.push(`${path}: plural without "other"`);
      out.set(path, [...new Set(Object.values(value).map(placeholders))].join(' | '));
    } else flatten(value, path, out, problems);
  }
  return { keys: out, problems };
}

const english = flatten(load('en'));
const problems = [...english.problems];

for (const code of readdirSync(LOCALES).map((file) => file.replace('.json', '')).filter((code) => code !== 'en')) {
  const other = flatten(load(code));
  problems.push(...other.problems.map((problem) => `${code}: ${problem}`));
  for (const [key, signature] of english.keys) {
    if (!other.keys.has(key)) problems.push(`${code}: missing ${key}`);
    else if (other.keys.get(key) !== signature.split(' | ')[0] && !other.keys.get(key).split(' | ').every((s) => signature.split(' | ').includes(s))) {
      problems.push(`${code}: ${key} placeholders {${other.keys.get(key)}} differ from English {${signature}}`);
    }
  }
  for (const key of other.keys.keys()) if (!english.keys.has(key)) problems.push(`${code}: extra key ${key}`);
}

function sources(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? sources(path) : /\.(jsx?|mjs)$/.test(name) ? [path] : [];
  });
}
for (const file of sources(SOURCE)) {
  for (const [, key] of readFileSync(file, 'utf8').matchAll(/\bt[x]?\(\s*'([\w.]+)'/g)) {
    if (!english.keys.has(key)) problems.push(`${file.replace(SOURCE, 'src/')}: unknown key ${key}`);
  }
}

if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}
console.log(`i18n: ${english.keys.size} keys, catalogs consistent.`);
