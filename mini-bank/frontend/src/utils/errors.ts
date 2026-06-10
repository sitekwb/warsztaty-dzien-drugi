/**
 * Unpack an error response into a human-readable string.
 *
 * Handles two FastAPI shapes:
 *  - HTTPException → { detail: "string message" }
 *  - Pydantic 422 → { detail: [{ loc, msg, type, ... }, ...] }
 *
 * Falls back to the provided string when neither shape matches.
 */
export function extractErrorDetail(e: unknown, fallback: string): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first && typeof first === "object" && "msg" in first) {
      const loc = Array.isArray((first as { loc?: unknown }).loc)
        ? ` (pole: ${((first as { loc: string[] }).loc).slice(-1)[0]})`
        : "";
      return `${(first as { msg: string }).msg}${loc}`;
    }
  }
  return fallback;
}
