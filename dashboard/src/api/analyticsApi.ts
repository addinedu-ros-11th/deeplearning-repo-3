// ============================================
// Analytics API - Functions to fetch analytics data
// Replace mock implementations with real FastAPI calls
// ============================================

import type {
  WeeklyDataPoint,
  HourlyDataPoint,
  CategoryData,
  AnalyticsStat,
} from "./types";

import {
  mockWeeklyData,
  mockHourlyCustomers,
  mockCategoryData,
  mockAnalyticsStats,
} from "./mockData";

// API Base URL - Change this when connecting to FastAPI
const API_BASE_URL = "/api";

// Simulated network delay for development
const simulateDelay = (ms: number = 100) => 
  new Promise(resolve => setTimeout(resolve, ms));

export interface AnalyticsDateRange {
  startDate?: string;
  endDate?: string;
}

/**
 * Fetch weekly revenue and customer data
 */
export async function fetchWeeklyData(range?: AnalyticsDateRange): Promise<WeeklyDataPoint[]> {
  // TODO: Replace with real API call
  // const params = new URLSearchParams();
  // if (range?.startDate) params.append("start", range.startDate);
  // if (range?.endDate) params.append("end", range.endDate);
  // const response = await fetch(`${API_BASE_URL}/analytics/weekly?${params}`);
  // return response.json();
  
  await simulateDelay();
  return mockWeeklyData;
}

/**
 * Fetch hourly customer flow data
 */
export async function fetchHourlyCustomers(date?: string): Promise<HourlyDataPoint[]> {
  // TODO: Replace with real API call
  // const params = date ? `?date=${date}` : "";
  // const response = await fetch(`${API_BASE_URL}/analytics/hourly-customers${params}`);
  // return response.json();
  
  await simulateDelay();
  return mockHourlyCustomers;
}

/**
 * Fetch category distribution data
 */
export async function fetchCategoryData(range?: AnalyticsDateRange): Promise<CategoryData[]> {
  // TODO: Replace with real API call
  // const params = new URLSearchParams();
  // if (range?.startDate) params.append("start", range.startDate);
  // if (range?.endDate) params.append("end", range.endDate);
  // const response = await fetch(`${API_BASE_URL}/analytics/categories?${params}`);
  // return response.json();
  
  await simulateDelay();
  return mockCategoryData;
}

/**
 * Fetch analytics statistics
 */
export async function fetchAnalyticsStats(range?: AnalyticsDateRange): Promise<AnalyticsStat[]> {
  // TODO: Replace with real API call
  // const params = new URLSearchParams();
  // if (range?.startDate) params.append("start", range.startDate);
  // if (range?.endDate) params.append("end", range.endDate);
  // const response = await fetch(`${API_BASE_URL}/analytics/stats?${params}`);
  // return response.json();
  
  await simulateDelay();
  return mockAnalyticsStats;
}

/**
 * Fetch all analytics data in a single request
 */
export async function fetchAnalyticsSummary(range?: AnalyticsDateRange): Promise<{
  weeklyData: WeeklyDataPoint[];
  hourlyCustomers: HourlyDataPoint[];
  categoryData: CategoryData[];
  stats: AnalyticsStat[];
}> {
  // TODO: Replace with real API call
  // const params = new URLSearchParams();
  // if (range?.startDate) params.append("start", range.startDate);
  // if (range?.endDate) params.append("end", range.endDate);
  // const response = await fetch(`${API_BASE_URL}/analytics/summary?${params}`);
  // return response.json();
  
  await simulateDelay();
  return {
    weeklyData: mockWeeklyData,
    hourlyCustomers: mockHourlyCustomers,
    categoryData: mockCategoryData,
    stats: mockAnalyticsStats,
  };
}
