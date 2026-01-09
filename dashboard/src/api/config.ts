// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1";
export const ADMIN_KEY = import.meta.env.VITE_ADMIN_KEY || "QkdRmt";
export const DEFAULT_STORE_CODE = import.meta.env.VITE_STORE_CODE || "STORE-01";

// Default headers for all API calls
export const getHeaders = () => ({
  "Content-Type": "application/json",
  "X-ADMIN-KEY": ADMIN_KEY,
});

/**
 * UTC 타임스탬프를 KST로 변환하여 포맷팅
 * DB에서 받은 UTC 시간을 한국 시간(KST, UTC+9)으로 표시
 */
export function formatToKST(utcTimestamp: string): string {
  // 서버에서 오는 타임스탬프가 UTC인데 'Z'가 없는 경우 추가
  let isoString = utcTimestamp;
  if (!isoString.endsWith("Z") && !isoString.includes("+")) {
    isoString = isoString + "Z";
  }

  const date = new Date(isoString);

  return date.toLocaleString("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

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
