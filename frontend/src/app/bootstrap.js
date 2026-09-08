// Django serialises everything a page needs into a <script type="application/json">
// block, so the app paints without a load-time API round trip.
let cached;

export function getBootstrap() {
  if (cached) return cached;

  const el = document.getElementById('planshift-bootstrap');
  try {
    cached = el ? JSON.parse(el.textContent || '{}') : {};
  } catch {
    cached = {};
  }
  return cached;
}
