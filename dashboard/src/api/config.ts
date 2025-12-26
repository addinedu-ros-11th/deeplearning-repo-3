// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
export const ADMIN_KEY = import.meta.env.VITE_ADMIN_KEY || "QkdRmt";
export const DEFAULT_STORE_CODE = import.meta.env.VITE_STORE_CODE || "STORE-01";

// Default headers for all API calls
export const getHeaders = () => ({
  "Content-Type": "application/json",
  "X-ADMIN-KEY": ADMIN_KEY,
});

// Fetch wrapper with default headers
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...getHeaders(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
