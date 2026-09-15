import { useEffect, useRef, useState } from 'react';

import { t } from '../i18n/index.js';
import { X } from './Icons.jsx';
import { isTopLayer, pushLayer } from './hooks.js';

// Modals stack: Escape and the backdrop only close the top-most one.
const BASE_Z_INDEX = 5000;

function useModalLayer(onClose) {
  const close = useRef(onClose);
  close.current = onClose;

  const [layer, setLayer] = useState({ depth: 1, isTop: () => true });

  useEffect(() => {
    const token = {};
    const entry = pushLayer(() => close.current?.(), token);
    setLayer({ depth: entry.depth, isTop: () => isTopLayer(token) });
    return entry.remove;
  }, []);

  return { zIndex: BASE_Z_INDEX + layer.depth, isTop: layer.isTop };
}

export function Modal({ title, onClose, children, footer, maxWidth = '500px', titleExtra = null }) {
  const { zIndex, isTop } = useModalLayer(onClose);

  return (
    <div
      className="modal-overlay"
      style={{ zIndex }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && isTop()) onClose?.();
      }}
    >
      <div className="modal" style={{ maxWidth }} role="dialog" aria-modal="true">
        <div className="modal-header">
          <div className="flex min-w-0 items-center gap-3">
            <h2 className="modal-title truncate">{title}</h2>
            {titleExtra}
          </div>
          <button className="modal-close" type="button" onClick={onClose} aria-label={t('common.close')}>
            <X />
          </button>
        </div>

        {children}

        {footer ? <div className="modal-footer">{footer}</div> : null}
      </div>
    </div>
  );
}

export function ConfirmModal({ title, message, detail, footnote, confirmText = t('common.yes'), destructive = false, onCancel, onConfirm }) {
  return (
    <Modal
      title={title}
      onClose={onCancel}
      footer={
        <>
          <button className="btn btn-outline" type="button" onClick={onCancel}>
            {t('common.no')}
          </button>
          <button className={`btn ${destructive ? 'btn-destructive' : 'btn-primary'}`} type="button" onClick={onConfirm}>
            {confirmText}
          </button>
        </>
      }
    >
      <div className="modal-body">
        <p className="text-sm">{message}</p>
        {detail ? <p className="mt-2 font-medium">{detail}</p> : null}
        {footnote ? <p className="mt-3 text-sm text-muted-foreground">{footnote}</p> : null}
      </div>
    </Modal>
  );
}
