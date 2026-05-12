export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function analysesStreamUrl() {
  return `${API_BASE}/api/v1/analyses`;
}

export function analysisUrl(id: string) {
  return `${API_BASE}/api/v1/analyses/${id}`;
}

export function graphUrl(id: string) {
  return `${API_BASE}/api/v1/graph/${id}`;
}
