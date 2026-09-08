/**
 * Dismissal stack. Escape closes the most recently opened layer only: a popover
 * inside a modal closes before the modal, and the top modal closes first.
 */
const layers = [];
let listening = false;

function onKeyDown(event) {
  if (event.key !== 'Escape' || layers.length === 0) return;

  event.preventDefault();
  layers[layers.length - 1].handler();
}

/** Register a dismissible layer; returns its depth and an unregister function. */
export function pushLayer(handler, token) {
  const layer = { handler, token };
  layers.push(layer);

  if (!listening) {
    document.addEventListener('keydown', onKeyDown);
    listening = true;
  }

  return {
    depth: layers.length,
    remove: () => {
      const index = layers.indexOf(layer);
      if (index >= 0) layers.splice(index, 1);
    },
  };
}

export function isTopLayer(token) {
  return layers.length > 0 && layers[layers.length - 1].token === token;
}
