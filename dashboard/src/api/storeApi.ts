// ============================================
// 매장 API - central-api 연결
// ============================================

import type { Device, DeviceType, StoreInfo, DeviceStatus } from "./types";
import { apiFetch } from "./config";

// central-api 응답 타입
interface StoreOut {
  store_id: number;
  store_code: string;
  name: string;
  created_at: string;
}

interface DeviceOut {
  device_id: number;
  store_id: number;
  device_code: string;
  device_type: "CHECKOUT" | "CCTV";
  status: "ACTIVE" | "INACTIVE" | "MAINTENANCE";
  stream_uri: string | null;
  config_json: unknown | null;
  created_at: string;
}

// central-api Device -> dashboard Device 변환
function deviceOutToDevice(device: DeviceOut): Device {
  // 디바이스 타입 매핑
  let type: DeviceType = "sensor";
  if (device.device_type === "CCTV") type = "camera";
  else if (device.device_type === "CHECKOUT") type = "display";

  // 상태 매핑
  let status: DeviceStatus = "online";
  if (device.status === "INACTIVE") status = "offline";
  else if (device.status === "MAINTENANCE") status = "warning";

  return {
    id: `DEV-${device.device_id}`,
    name: device.device_code,
    type,
    location: `Store ${device.store_id}`,
    status,
    lastActive: new Date(device.created_at).toLocaleString("ko-KR"),
  };
}

export interface DeviceStats {
  online: number;
  warning: number;
  offline: number;
  total: number;
}

// 현재 선택된 매장 코드 (기본값)
let currentStoreCode = "STORE-01";

export function setCurrentStoreCode(code: string) {
  currentStoreCode = code;
}

/**
 * 매장 정보 조회 (stores API 연결)
 */
export async function fetchStoreInfo(): Promise<StoreInfo> {
  const stores = await apiFetch<StoreOut[]>("/stores");

  // 현재 매장 찾기
  const store = stores.find(s => s.store_code === currentStoreCode) || stores[0];

  if (!store) {
    return {
      name: "매장 없음",
      address: "-",
      operatingHours: "-",
      totalTables: 0,
      totalDevices: 0,
      onlineDevices: 0,
    };
  }

  // 디바이스 정보도 함께 조회
  const devices = await fetchDevices();
  const onlineDevices = devices.filter(d => d.status === "online").length;

  return {
    name: store.name,
    address: `Store Code: ${store.store_code}`,
    operatingHours: "09:00 - 22:00", // central-api에 없음 - 기본값
    totalTables: 0, // central-api에 없음
    totalDevices: devices.length,
    onlineDevices,
  };
}

/**
 * 디바이스 목록 조회 (stores/{code}/devices API 연결)
 */
export async function fetchDevices(): Promise<Device[]> {
  const devices = await apiFetch<DeviceOut[]>(`/stores/${currentStoreCode}/devices`);
  return devices.map(deviceOutToDevice);
}

/**
 * 디바이스 통계 조회
 */
export async function fetchDeviceStats(): Promise<DeviceStats> {
  const devices = await fetchDevices();

  return {
    online: devices.filter(d => d.status === "online").length,
    warning: devices.filter(d => d.status === "warning").length,
    offline: devices.filter(d => d.status === "offline").length,
    total: devices.length,
  };
}

/**
 * 매장 정보 수정 (central-api 미지원 - 임시 구현)
 */
export async function updateStoreInfo(updates: Partial<StoreInfo>): Promise<StoreInfo> {
  console.warn("updateStoreInfo: central-api에서 직접 지원하지 않음");
  const current = await fetchStoreInfo();
  return { ...current, ...updates };
}

/**
 * 디바이스 ID로 조회
 */
export async function fetchDeviceById(deviceId: string): Promise<Device | null> {
  const devices = await fetchDevices();
  return devices.find(d => d.id === deviceId) || null;
}

/**
 * 디바이스 상태 수정 (central-api 미지원 - 임시 구현)
 */
export async function updateDeviceStatus(
  deviceId: string,
  status: DeviceStatus
): Promise<Device> {
  console.warn("updateDeviceStatus: central-api에서 직접 지원하지 않음");

  const device = await fetchDeviceById(deviceId);
  if (!device) throw new Error("디바이스를 찾을 수 없습니다");

  return { ...device, status };
}
