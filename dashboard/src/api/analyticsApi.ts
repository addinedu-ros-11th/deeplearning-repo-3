// ============================================
// Analytics API - central-api 연결
// ============================================

import type {
  WeeklyDataPoint,
  HourlyDataPoint,
  CategoryData,
  AnalyticsStat,
} from "./types";
import { apiFetch, DEFAULT_STORE_CODE } from "./config";

/**
 * 주간 매출/고객 데이터 조회
 */
export async function fetchWeeklyData(
  storeCode: string = DEFAULT_STORE_CODE
): Promise<WeeklyDataPoint[]> {
  const params = new URLSearchParams({ store_code: storeCode });
  const data = await apiFetch<WeeklyDataPoint[]>(
    `/dashboards/analytics/weekly?${params}`
  );
  return data;
}

/**
 * 시간대별 고객 수 조회
 */
export async function fetchHourlyCustomers(
  storeCode: string = DEFAULT_STORE_CODE
): Promise<HourlyDataPoint[]> {
  const params = new URLSearchParams({ store_code: storeCode });
  const data = await apiFetch<HourlyDataPoint[]>(
    `/dashboards/analytics/hourly-customers?${params}`
  );
  return data;
}

/**
 * 카테고리별 판매 비율 조회
 */
export async function fetchCategoryData(
  storeCode: string = DEFAULT_STORE_CODE
): Promise<CategoryData[]> {
  const params = new URLSearchParams({ store_code: storeCode });
  const data = await apiFetch<CategoryData[]>(
    `/dashboards/analytics/categories?${params}`
  );
  return data;
}

/**
 * 분석 통계 조회
 */
export async function fetchAnalyticsStats(
  storeCode: string = DEFAULT_STORE_CODE
): Promise<AnalyticsStat[]> {
  const params = new URLSearchParams({ store_code: storeCode });
  const data = await apiFetch<AnalyticsStat[]>(
    `/dashboards/analytics/stats?${params}`
  );
  return data;
}

/**
 * 분석 전체 데이터 조회
 */
export async function fetchAnalyticsSummary(
  storeCode: string = DEFAULT_STORE_CODE
): Promise<{
  weeklyData: WeeklyDataPoint[];
  hourlyCustomers: HourlyDataPoint[];
  categoryData: CategoryData[];
  stats: AnalyticsStat[];
}> {
  const [weeklyData, hourlyCustomers, categoryData, stats] = await Promise.all([
    fetchWeeklyData(storeCode),
    fetchHourlyCustomers(storeCode),
    fetchCategoryData(storeCode),
    fetchAnalyticsStats(storeCode),
  ]);

  return {
    weeklyData,
    hourlyCustomers,
    categoryData,
    stats,
  };
}
