// ============================================
// Dashboard API - Functions to fetch dashboard data
// Replace mock implementations with real FastAPI calls
// ============================================

import type {
  KPIData,
  Transaction,
  TableData,
  AlertSummary,
  HourlyRevenuePoint,
  ProductSalesData,
  DashboardSummary,
} from "./types";

import {
  mockKPIs,
  mockTransactionsShort,
  mockTables,
  mockAlertsSummary,
  mockHourlyRevenue,
  mockProductSales,
} from "./mockData";

// API Base URL - Change this when connecting to FastAPI
const API_BASE_URL = "/api";

// Simulated network delay for development
const simulateDelay = (ms: number = 100) => 
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * Fetch KPI data for the dashboard
 */
export async function fetchKPIs(): Promise<KPIData[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/dashboard/kpis`);
  // return response.json();
  
  await simulateDelay();
  return mockKPIs;
}

/**
 * Fetch recent transactions for the dashboard
 */
export async function fetchRecentTransactions(): Promise<Transaction[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/transactions/recent`);
  // return response.json();
  
  await simulateDelay();
  return mockTransactionsShort;
}

/**
 * Fetch table floor plan data
 */
export async function fetchTables(): Promise<TableData[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/tables`);
  // return response.json();
  
  await simulateDelay();
  return mockTables;
}

/**
 * Fetch alerts summary for the dashboard
 */
export async function fetchAlertsSummary(): Promise<AlertSummary[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/alerts/summary`);
  // return response.json();
  
  await simulateDelay();
  return mockAlertsSummary;
}

/**
 * Fetch hourly revenue data
 */
export async function fetchHourlyRevenue(): Promise<HourlyRevenuePoint[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/analytics/hourly-revenue`);
  // return response.json();
  
  await simulateDelay();
  return mockHourlyRevenue;
}

/**
 * Fetch product sales data
 */
export async function fetchProductSales(): Promise<ProductSalesData[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/analytics/product-sales`);
  // return response.json();
  
  await simulateDelay();
  return mockProductSales;
}

/**
 * Fetch all dashboard data in a single request
 * More efficient for initial load
 */
export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
  // return response.json();
  
  await simulateDelay();
  return {
    kpis: mockKPIs,
    tables: mockTables,
    transactions: mockTransactionsShort,
    alerts: mockAlertsSummary,
    hourlyRevenue: mockHourlyRevenue,
    productSales: mockProductSales,
  };
}
