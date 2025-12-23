// ============================================
// Store API - Functions to manage store and devices
// Replace mock implementations with real FastAPI calls
// ============================================

import type { Device, StoreInfo, DeviceStatus } from "./types";
import { mockDevices, mockStoreInfo } from "./mockData";

// API Base URL - Change this when connecting to FastAPI
const API_BASE_URL = "/api";

// Simulated network delay for development
const simulateDelay = (ms: number = 100) => 
  new Promise(resolve => setTimeout(resolve, ms));

export interface DeviceStats {
  online: number;
  warning: number;
  offline: number;
  total: number;
}

/**
 * Fetch store information
 */
export async function fetchStoreInfo(): Promise<StoreInfo> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/store/info`);
  // return response.json();
  
  await simulateDelay();
  return mockStoreInfo;
}

/**
 * Fetch all devices
 */
export async function fetchDevices(): Promise<Device[]> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/devices`);
  // return response.json();
  
  await simulateDelay();
  return mockDevices;
}

/**
 * Get device statistics
 */
export async function fetchDeviceStats(): Promise<DeviceStats> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/devices/stats`);
  // return response.json();
  
  await simulateDelay();
  
  const devices = mockDevices;
  return {
    online: devices.filter(d => d.status === "online").length,
    warning: devices.filter(d => d.status === "warning").length,
    offline: devices.filter(d => d.status === "offline").length,
    total: devices.length,
  };
}

/**
 * Update store information
 */
export async function updateStoreInfo(updates: Partial<StoreInfo>): Promise<StoreInfo> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/store/info`, {
  //   method: "PATCH",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify(updates),
  // });
  // return response.json();
  
  await simulateDelay();
  return { ...mockStoreInfo, ...updates };
}

/**
 * Get device by ID
 */
export async function fetchDeviceById(deviceId: string): Promise<Device | null> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/devices/${deviceId}`);
  // if (!response.ok) return null;
  // return response.json();
  
  await simulateDelay();
  return mockDevices.find(d => d.id === deviceId) || null;
}

/**
 * Update device status
 */
export async function updateDeviceStatus(
  deviceId: string, 
  status: DeviceStatus
): Promise<Device> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/devices/${deviceId}/status`, {
  //   method: "PATCH",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ status }),
  // });
  // return response.json();
  
  await simulateDelay();
  
  const device = mockDevices.find(d => d.id === deviceId);
  if (!device) throw new Error("Device not found");
  
  return { ...device, status };
}
