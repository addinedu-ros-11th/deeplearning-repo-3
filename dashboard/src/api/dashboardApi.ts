// ============================================
// 대시보드 API - central-api 연결
// ============================================

import type {
  KPIData,
  AlertSummary,
  AlertSeverity,
  HourlyRevenuePoint,
  ProductSalesData,
  DashboardSummary,
  OrderHdrOut,
  ReviewOut,
} from "./types";
import { apiFetch, DEFAULT_STORE_CODE, formatToKST } from "./config";
import { orderToTransaction } from "./paymentApi";

// Top Menu API 응답 타입 (dashboardApi 전용)
interface TopMenuRow {
  item_id: number;
  name_kor: string;
  name_eng: string;
  qty: number;
  amount_won: number;
}

// KPI API 응답 타입
interface KPIOut {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  trend: "up" | "down" | "neutral";
  variant: "revenue" | "customers" | "occupancy" | "alerts";
}

/**
 * KPI 데이터 조회 (kpis API 연결)
 */
export async function fetchKPIs(storeCode: string = DEFAULT_STORE_CODE): Promise<KPIData[]> {
  const params = new URLSearchParams({ store_code: storeCode });
  const kpis = await apiFetch<KPIOut[]>(`/dashboards/kpis?${params}`);
  return kpis;
}

/**
 * 최근 트랜잭션 조회 (orders API 연결)
 */
export async function fetchRecentTransactions() {
  const orders = await apiFetch<OrderHdrOut[]>("/orders");
  // 최근 5개만 반환, 대시보드에서는 줄바꿈으로 상품 구분
  return orders.slice(0, 5).map(order => orderToTransaction(order, "\n"));
}

/**
 * 알림 요약 조회 (reviews API 연결)
 */
export async function fetchAlertsSummary(): Promise<AlertSummary[]> {
  const reviews = await apiFetch<ReviewOut[]>("/reviews?status=OPEN");

  return reviews.slice(0, 5).map(review => {
    let severity: AlertSeverity = "normal";
    let message = `세션 ${review.session_id} 검토 필요: ${review.reason}`;
    let type = review.reason;

    if (review.reason === "ADMIN_CALL") {
      severity = "warning";
      message = "관리자 호출 요청";
      type = "시스템";
    } else if (review.reason === "REVIEW") {
      severity = "warning";
      type = "결제";
    } else if (review.reason === "UNKNOWN") {
      severity = "critical";
      message = "알 수 없는 아이템이 감지되었습니다";
      type = "결제";
    }

    // top_k_json 파싱하여 메시지 생성
    if (review.reason !== "ADMIN_CALL" && review.reason !== "UNKNOWN" && review.top_k_json && Array.isArray(review.top_k_json)) {
      const itemNames = review.top_k_json
        .map((item: any) => item.name_kor || `#${item.item_id}`)
        .filter((name: any) => name !== undefined)
        .slice(0, 3); // 최대 3개만 표시

      if (itemNames.length > 0) {
        message = `인식된 아이템의 추론 확률이 낮습니다: ${itemNames.join(", ")}`;
      }
    }

    return {
      id: review.review_id,
      severity,
      type,
      message,
      timestamp: formatToKST(review.created_at),
    };
  });
}

/**
 * 시간대별 매출 조회 (hourly-revenue API 연결)
 */
export async function fetchHourlyRevenue(storeCode: string = DEFAULT_STORE_CODE): Promise<HourlyRevenuePoint[]> {
  const params = new URLSearchParams({ store_code: storeCode });
  const data = await apiFetch<HourlyRevenuePoint[]>(`/dashboards/hourly-revenue?${params}`);
  return data;
}

/**
 * 상품별 매출 조회 (top-menu API 연결)
 */
export async function fetchProductSales(storeCode: string = DEFAULT_STORE_CODE): Promise<ProductSalesData[]> {
  // 오늘 날짜 기준으로 조회
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString();
  const to = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1).toISOString();

  const params = new URLSearchParams({
    store_code: storeCode,
    from_: from,
    to: to,
    limit: "10",
  });

  const topMenu = await apiFetch<TopMenuRow[]>(`/dashboards/top-menu?${params}`);

  // 전체 수량 계산
  const totalQty = topMenu.reduce((sum, item) => sum + item.qty, 0);

  return topMenu.map(item => ({
    name: item.name_kor,
    nameEn: item.name_eng,
    value: item.qty,
    percentage: totalQty > 0 ? Math.round((item.qty / totalQty) * 100) : 0,
  }));
}

/**
 * 대시보드 전체 데이터 조회
 */
export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  // 병렬로 모든 데이터 조회
  const [kpis, transactions, alerts, hourlyRevenue, productSales] = await Promise.all([
    fetchKPIs(),
    fetchRecentTransactions(),
    fetchAlertsSummary(),
    fetchHourlyRevenue(),
    fetchProductSales(),
  ]);

  return {
    kpis,
    transactions,
    alerts,
    hourlyRevenue,
    productSales,
  };
}
