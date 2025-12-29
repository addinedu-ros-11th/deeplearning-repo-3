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
import { apiFetch, DEFAULT_STORE_CODE } from "./config";
import { orderToTransaction } from "./paymentApi";

// Top Menu API 응답 타입 (dashboardApi 전용)
interface TopMenuRow {
  item_id: number;
  name: string;
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
    if (review.reason === "REVIEW") severity = "critical";
    else if (review.reason === "UNKNOWN") severity = "warning";

    return {
      id: review.review_id,
      severity,
      type: review.reason,
      message: `세션 ${review.session_id} 검토 필요`,
      timestamp: new Date(review.created_at).toLocaleString("ko-KR"),
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
    name: item.name,
    nameEn: item.name, // 영문명이 없으므로 동일하게 사용
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
