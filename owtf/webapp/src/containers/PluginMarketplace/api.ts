import { API_BASE_URL } from "../../utils/constants";

function authHeaders(): HeadersInit {
  return {
    Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
  };
}

export interface PluginListParams {
  status?: string;
  category?: string;
  group?: string;
  type?: string;
  min_rating?: number;
  q?: string;
  limit?: number;
  offset?: number;
}

export async function fetchCommunityPlugins(params: PluginListParams = {}): Promise<any> {
  const url = new URL(`${API_BASE_URL}community-plugins/`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.append(k, String(v));
  });
  const res = await fetch(url.toString(), { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch plugins: ${res.status}`);
  return res.json();
}

export async function fetchCommunityPluginDetail(id: number): Promise<any> {
  const res = await fetch(`${API_BASE_URL}community-plugins/${id}/`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Plugin not found: ${res.status}`);
  return res.json();
}

export async function uploadCommunityPlugin(formData: FormData): Promise<any> {
  const res = await fetch(`${API_BASE_URL}community-plugins/upload/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
    body: formData,
  });
  const json = await res.json();
  if (!res.ok) throw json;
  return json;
}

export async function runCommunityPlugin(id: number, targetUrl: string): Promise<any> {
  // Backend endpoint is /test-run/. The old /run/ alias was removed once
  // the frontend was ready to switch, so this must stay on /test-run/.
  const res = await fetch(`${API_BASE_URL}community-plugins/${id}/test-run/`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ target_url: targetUrl }),
  });
  const json = await res.json();
  if (!res.ok) throw json;
  return json;
}
