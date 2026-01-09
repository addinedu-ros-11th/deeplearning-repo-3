// ============================================
// 알림 API - central-api /reviews + /cctv/events 엔드포인트 연결
// ============================================

import type { Alert, AlertSeverity, AlertCategory, ReviewOut, CctvEventOut, CctvEventType } from "./types";
import { apiFetch, formatToKST } from "./config";

// central-api Review -> dashboard Alert 변환
function reviewToAlert(review: ReviewOut): Alert {
  // reason에 따라 심각도 결정
  let type: AlertSeverity = "normal";
  let message = `세션 ${review.session_id} 검토 필요: ${review.reason}`;
  let category: AlertCategory = "payment";

  if (review.reason === "ADMIN_CALL") {
    type = "warning";
    message = "관리자 호출 요청";
    category = "system";
  } else if (review.reason === "REVIEW") {
    type = "warning";
  } else if (review.reason === "UNKNOWN") {
    type = "critical";
    message = "알 수 없는 아이템이 감지되었습니다";
  }

  // top_k_json 파싱하여 메시지 생성 (ADMIN_CALL이 아닌 경우만)
  if (review.reason !== "ADMIN_CALL" && review.top_k_json && Array.isArray(review.top_k_json)) {
    const itemNames = review.top_k_json
      .map((item: any) => item.name_kor || `#${item.item_id}`)
      .filter((name: any) => name !== undefined)
      .slice(0, 3); // 최대 3개만 표시

    if (itemNames.length > 0) {
      message = `인식된 아이템의 추론 확률이 낮습니다: ${itemNames.join(", ")}`;
    }
  }

  // 위치 정보 구성
  let location = `Session #${review.session_id}`;
  if (review.store_name || review.device_code) {
    const parts = [];
    if (review.store_name) parts.push(review.store_name);
    if (review.device_code) parts.push(review.device_code);
    location = parts.join(" / ");
  }

  return {
    id: `REV-${review.review_id}`,
    type,
    category,
    message,
    location,
    timestamp: formatToKST(review.created_at),
    isRead: review.status === "RESOLVED",
    review_id: review.review_id,  // 확정 처리에 필요
    top_k_json: review.top_k_json,  // 확정 처리에 필요
  };
}

// CCTV 이벤트 타입 -> 심각도 매핑
function getEventSeverity(eventType: CctvEventType): AlertSeverity {
  switch (eventType) {
    case "VIOLENCE":
    case "VANDALISM":
      return "critical";
    case "FALL":
      return "warning";
    case "WHEELCHAIR":
      return "normal";
    default:
      return "warning";
  }
}

// CCTV 이벤트 타입 -> 한글 메시지
function getEventMessage(eventType: CctvEventType): string {
  switch (eventType) {
    case "VIOLENCE":
      return "폭력 행위 감지";
    case "VANDALISM":
      return "기물 파손 감지";
    case "FALL":
      return "낙상 감지";
    case "WHEELCHAIR":
      return "휠체어 이용자 감지";
    default:
      return "CCTV 이벤트 감지";
  }
}

// gs://bucket/path → https://storage.googleapis.com/bucket/path
function gcsToPublicUrl(gcsUri: string): string {
  if (gcsUri.startsWith("gs://")) {
    return gcsUri.replace("gs://", "https://storage.googleapis.com/");
  }
  return gcsUri;
}

// central-api CctvEvent -> dashboard Alert 변환
function cctvEventToAlert(event: CctvEventOut): Alert {
  const type = getEventSeverity(event.event_type);
  const message = getEventMessage(event.event_type);

  // 첫 번째 클립의 GCS URI를 공개 URL로 변환
  const clipUrl = event.clips.length > 0
    ? gcsToPublicUrl(event.clips[0].clip_gcs_uri)
    : undefined;

  return {
    id: `CCTV-${event.event_id}`,
    type,
    category: event.event_type === "VANDALISM" ? "security" : "safety",
    message,
    location: `CCTV Device #${event.cctv_device_id}`,
    timestamp: formatToKST(event.created_at),
    isRead: event.status !== "OPEN",
    event_id: event.event_id,
    clip_url: clipUrl,
    event_type: event.event_type,
  };
}

export interface AlertFilter {
  type?: AlertSeverity | "all";
  category?: AlertCategory | "all";
  status?: "OPEN" | "RESOLVED";
}

export interface AlertStats {
  critical: number;
  warning: number;
  normal: number;
  unread: number;
  total: number;
}

/**
 * 알림 목록 조회 (필터 적용)
 * Review + CCTV 이벤트를 통합하여 반환
 */
export async function fetchAlerts(filter?: AlertFilter): Promise<Alert[]> {
  // 기본적으로 OPEN 상태 조회
  const status = filter?.status || "OPEN";

  // Review와 CCTV 이벤트를 병렬로 조회
  const [reviews, cctvEvents] = await Promise.all([
    apiFetch<ReviewOut[]>(`/reviews?status=${status}`),
    apiFetch<CctvEventOut[]>(`/cctv/events`).catch((err) => {
      console.error("CCTV API error:", err);
      return [] as CctvEventOut[];
    }),
  ]);

  console.log("CCTV Events:", cctvEvents);
  console.log("CCTV clips:", cctvEvents.map(e => e.clips));

  // 각각 Alert로 변환
  const reviewAlerts = reviews.map(reviewToAlert);
  const cctvAlerts = cctvEvents
    .filter(e => status === "OPEN" ? e.status === "OPEN" : e.status !== "OPEN")
    .map(cctvEventToAlert);

  console.log("CCTV Alerts:", cctvAlerts);

  // 합치고 시간순 정렬 (최신 먼저)
  let result = [...reviewAlerts, ...cctvAlerts].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });

  // 클라이언트 측 필터링
  if (filter?.type && filter.type !== "all") {
    result = result.filter(a => a.type === filter.type);
  }

  if (filter?.category && filter.category !== "all") {
    result = result.filter(a => a.category === filter.category);
  }

  return result;
}

/**
 * 알림 통계 조회
 */
export async function fetchAlertStats(): Promise<AlertStats> {
  // OPEN 상태 리뷰 + CCTV 이벤트 조회
  const [reviews, cctvEvents] = await Promise.all([
    apiFetch<ReviewOut[]>("/reviews?status=OPEN"),
    apiFetch<CctvEventOut[]>("/cctv/events").catch(() => [] as CctvEventOut[]),
  ]);

  const reviewAlerts = reviews.map(reviewToAlert);
  const cctvAlerts = cctvEvents
    .filter(e => e.status === "OPEN")
    .map(cctvEventToAlert);

  const alerts = [...reviewAlerts, ...cctvAlerts];

  return {
    critical: alerts.filter(a => a.type === "critical").length,
    warning: alerts.filter(a => a.type === "warning").length,
    normal: alerts.filter(a => a.type === "normal").length,
    unread: alerts.filter(a => !a.isRead).length,
    total: alerts.length,
  };
}

/**
 * 알림 읽음 처리 (리뷰 상태를 RESOLVED로 변경)
 */
export async function markAlertAsRead(alertId: string): Promise<Alert> {
  const reviewId = alertId.replace("REV-", "");

  const review = await apiFetch<ReviewOut>(`/reviews/${reviewId}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: "RESOLVED",
      resolved_by: "dashboard_user",
    }),
  });

  return reviewToAlert(review);
}

/**
 * 알림 확인 처리 (리뷰 상태를 RESOLVED로 변경)
 */
export async function acknowledgeAlert(alertId: string): Promise<Alert> {
  return markAlertAsRead(alertId);
}

/**
 * 리뷰 확정 처리 (top_k_json을 confirmed_items_json으로 사용)
 */
export async function confirmReview(reviewId: number, topKJson: any[]): Promise<ReviewOut> {
  // top_k_json을 confirmed_items_json 형식으로 변환
  // [{"item_id": 101, "distance": 0.14}, ...] -> [{"item_id": 101, "qty": 1}, ...]
  const confirmedItems = topKJson.map((item: any) => ({
    item_id: item.item_id,
    qty: 1, // 기본 수량 1
  }));

  const review = await apiFetch<ReviewOut>(`/reviews/${reviewId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      status: "RESOLVED",
      resolved_by: "dashboard_user",
      confirmed_items_json: confirmedItems,
    }),
  });

  return review;
}

/**
 * 모든 알림 읽음 처리 (central-api에서 미지원 - 개별 처리)
 */
export async function markAllAlertsAsRead(): Promise<{ success: boolean }> {
  const reviews = await apiFetch<ReviewOut[]>("/reviews?status=OPEN");

  // 각 리뷰를 RESOLVED로 변경
  await Promise.all(
    reviews.map(review =>
      apiFetch(`/reviews/${review.review_id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: "RESOLVED",
          resolved_by: "dashboard_user",
        }),
      })
    )
  );

  return { success: true };
}
