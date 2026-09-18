// What an open page does when the session behind it ends somewhere else: signed out in
// another tab, signed out by a role change, or the account erased. The server pushes
// `session.ended` over the socket; without it the tab would sit on a page that still
// looks signed in until something on it failed.
import { getBootstrap } from './http.js';
import { useLiveEvents } from './live.js';

/** Leave for the sign-in page, replacing this entry so Back cannot come back to it. */
function toSignIn() {
  window.location.replace(getBootstrap().urls.login);
}

/**
 * Watch for the end of this page's session. Used once, by `AppShell`, so every signed-in
 * page has it; the legal pages are public and have no session to lose.
 */
export function useSessionGuard() {
  useLiveEvents((event) => event.type === 'session.ended' && toSignIn(), {
    enabled: Boolean(getBootstrap().user),
  });
}

/**
 * Reload a page the browser restored from its back/forward cache instead of showing it as
 * it was. Signed-in responses say `no-store`, which keeps them out of that cache in Chrome
 * and Firefox; Safari is laxer, and this is the part that does not depend on the browser.
 *
 * Installed once, from the entry point, so it also covers pages with no live socket.
 */
export function watchBackForwardCache() {
  window.addEventListener('pageshow', (event) => {
    if (event.persisted) window.location.reload();
  });
}
