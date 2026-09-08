import { getCsrfToken } from '../app/http.js';

export function CsrfInput() {
  return <input type="hidden" name="csrfmiddlewaretoken" value={getCsrfToken()} readOnly />;
}

/**
 * Hidden POST form used for actions the server answers with a redirect and a
 * flash message (delete, publish, reset password). Submit it through the ref.
 */
export function PostForm({ formRef, action, fields = {}, id }) {
  return (
    <form ref={formRef} id={id} method="post" action={action} className="hidden">
      <CsrfInput />
      {Object.entries(fields).map(([name, value]) => (
        <input key={name} type="hidden" name={name} value={value} readOnly />
      ))}
    </form>
  );
}
