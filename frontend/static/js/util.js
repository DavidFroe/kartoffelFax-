export function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export async function api(path, options = {}) {
  const init = { ...options };
  if (init.json !== undefined) {
    init.method = init.method ?? "POST";
    init.headers = { "Content-Type": "application/json", ...(init.headers ?? {}) };
    init.body = JSON.stringify(init.json);
    delete init.json;
  }
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => d.msg).join("; ");
    } catch {
      // non-JSON error body (e.g. unhandled server error); keep the status text
    }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

export function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("de-DE");
}

export const inputClass =
  "w-full rounded border border-neutral-300 bg-white px-2 py-1.5 text-sm focus:border-amber-500 focus:outline-none";
export const buttonClass = "rounded bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700";
export const secondaryButtonClass =
  "rounded border border-neutral-300 bg-white px-3 py-1.5 text-sm hover:bg-neutral-100";
