// ============================================
// Alerts API - Functions to manage alerts
// Replace mock implementations with real FastAPI calls
// ============================================

import type { Alert, AlertSeverity, AlertCategory } from "./types";
import { mockAlertsFull } from "./mockData";

// API Base URL - Change this when connecting to FastAPI
const API_BASE_URL = "/api";

// Simulated network delay for development
const simulateDelay = (ms: number = 100) => 
  new Promise(resolve => setTimeout(resolve, ms));

export interface AlertFilter {
  type?: AlertSeverity | "all";
  category?: AlertCategory | "all";
}

export interface AlertStats {
  critical: number;
  warning: number;
  normal: number;
  unread: number;
  total: number;
}

/**
 * Fetch all alerts with optional filters
 */
export async function fetchAlerts(filter?: AlertFilter): Promise<Alert[]> {
  // TODO: Replace with real API call
  // const params = new URLSearchParams();
  // if (filter?.type && filter.type !== "all") params.append("type", filter.type);
  // if (filter?.category && filter.category !== "all") params.append("category", filter.category);
  // const response = await fetch(`${API_BASE_URL}/alerts?${params}`);
  // return response.json();
  
  await simulateDelay();
  
  let result = [...mockAlertsFull];
  
  if (filter?.type && filter.type !== "all") {
    result = result.filter(a => a.type === filter.type);
  }
  
  if (filter?.category && filter.category !== "all") {
    result = result.filter(a => a.category === filter.category);
  }
  
  return result;
}

/**
 * Get alert statistics
 */
export async function fetchAlertStats(): Promise<AlertStats> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/alerts/stats`);
  // return response.json();
  
  await simulateDelay();
  
  const alerts = mockAlertsFull;
  return {
    critical: alerts.filter(a => a.type === "critical").length,
    warning: alerts.filter(a => a.type === "warning").length,
    normal: alerts.filter(a => a.type === "normal").length,
    unread: alerts.filter(a => !a.isRead).length,
    total: alerts.length,
  };
}

/**
 * Mark an alert as read
 */
export async function markAlertAsRead(alertId: string): Promise<Alert> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/read`, {
  //   method: "POST",
  // });
  // return response.json();
  
  await simulateDelay();
  
  const alert = mockAlertsFull.find(a => a.id === alertId);
  if (!alert) throw new Error("Alert not found");
  
  return { ...alert, isRead: true };
}

/**
 * Acknowledge/confirm an alert
 */
export async function acknowledgeAlert(alertId: string): Promise<Alert> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/acknowledge`, {
  //   method: "POST",
  // });
  // return response.json();
  
  await simulateDelay();
  
  const alert = mockAlertsFull.find(a => a.id === alertId);
  if (!alert) throw new Error("Alert not found");
  
  return { ...alert, isRead: true };
}

/**
 * Mark all alerts as read
 */
export async function markAllAlertsAsRead(): Promise<{ success: boolean }> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/alerts/read-all`, {
  //   method: "POST",
  // });
  // return response.json();
  
  await simulateDelay();
  return { success: true };
}
