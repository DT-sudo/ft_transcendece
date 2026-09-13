// Django serialises everything a page needs into a <script type="application/json">
// block, so the app paints without a load-time API round trip.
let bootstrap;

export function getBootstrap() {
  if (!bootstrap) {
    bootstrap = JSON.parse(document.getElementById('planshift-bootstrap').textContent);
  }
  return bootstrap;
}

// "/manager/shifts/0/delete/" + 12 -> "/manager/shifts/12/delete/"
export const urlFromTemplate = (template, id) => template.replace('/0/', `/${id}/`);

/**
 * POST `fields` as a regular form submission, for actions the server answers
 * with a redirect and a flash message (delete, publish, reset password, logout).
 */
export function submitPost(action, fields = {}) {
  const form = document.createElement('form');
  form.method = 'post';
  form.action = action;
  form.hidden = true;

  for (const [name, value] of Object.entries({ csrfmiddlewaretoken: getBootstrap().csrfToken, ...fields })) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    form.append(input);
  }

  document.body.append(form);
  form.submit();
}

/** GET a JSON endpoint; throws on failure. */
export async function getJSON(url) {
  const response = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error('Request failed.');
  return response.json();
}

/** POST as a fetch and return the JSON body; throws with the server's message on failure. */
export async function postForm(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      Accept: 'application/json',
      'X-CSRFToken': getBootstrap().csrfToken,
    },
    body: new URLSearchParams(data),
  });

  const payload = await response.json().catch(() => ({}));
  if (response.ok) return payload;

  throw new Error(payload.error || 'Request failed.');
}
