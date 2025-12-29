// ============================================
// 알림 API - central-api /reviews 엔드포인트 연결
// ============================================

import type { Alert, AlertSeverity, AlertCategory, ReviewOut } from "./types";
import { apiFetch } from "./config";

// central-api Review -> dashboard Alert 변환
function reviewToAlert(review: ReviewOut): Alert {
  // reason에 따라 심각도 결정
  let type: AlertSeverity = "normal";
  if (review.reason === "REVIEW") type = "critical";
  else if (review.reason === "UNKNOWN") type = "warning";

  // top_k_json 파싱하여 메시지 생성
  let message = `세션 ${review.session_id} 검토 필요: ${review.reason}`;
  if (review.top_k_json && Array.isArray(review.top_k_json)) {
    const itemIds = review.top_k_json
      .map((item: any) => item.item_id)
      .filter((id: any) => id !== undefined)
      .slice(0, 3); // 최대 3개만 표시

    if (itemIds.length > 0) {
      message = `인식된 아이템: ${itemIds.map((id: number) => `#${id}`).join(", ")} (${review.reason})`;
    }
  }

  return {
    id: `REV-${review.review_id}`,
    type,
    category: "payment", // 리뷰는 결제 관련
    message,
    location: `Session #${review.session_id}`,
    timestamp: new Date(review.created_at).toLocaleString("ko-KR"),
    isRead: review.status === "RESOLVED",
    review_id: review.review_id,  // 확정 처리에 필요
    top_k_json: review.top_k_json,  // 확정 처리에 필요
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
 */
export async function fetchAlerts(filter?: AlertFilter): Promise<Alert[]> {
  // 기본적으로 OPEN 상태 조회
  const status = filter?.status || "OPEN";
  const reviews = await apiFetch<ReviewOut[]>(`/reviews?status=${status}`);

  let result = reviews.map(reviewToAlert);

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
  // OPEN 상태 리뷰만 조회
  const reviews = await apiFetch<ReviewOut[]>("/reviews?status=OPEN");
  const alerts = reviews.map(reviewToAlert);

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
