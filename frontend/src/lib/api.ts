/**
 * Optional full API origin when the SPA is served separately from FastAPI,
 * for example production static hosting. Example: http://127.0.0.1:8000
 * Leave unset during local dev so requests use /api paths and Vite proxy.
 */
export function apiUrl(path: string): string {
  const raw =
    typeof import.meta.env.VITE_API_BASE_URL === "string"
      ? import.meta.env.VITE_API_BASE_URL.trim()
      : "";
  const prefix = raw.replace(/\/$/, "");
  if (!prefix) {
    return path.startsWith("/") ? path : `/${path}`;
  }
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${prefix}${p}`;
}

export async function postForm(path: string, formData: FormData): Promise<unknown> {
  const response = await fetch(apiUrl(path), {
    method: "POST",
    body: formData,
    headers: { Accept: "application/json" },
  });
  let data: unknown;
  const text = await response.text();
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error("Server returned invalid JSON.");
  }
  const obj = data && typeof data === "object" ? (data as Record<string, unknown>) : {};
  if ("error" in obj && typeof obj.error === "string") {
    throw new Error(obj.error);
  }
  if (!response.ok) {
    const detail = typeof obj.detail === "string" ? obj.detail : "Request failed.";
    throw new Error(detail);
  }
  return data;
}
