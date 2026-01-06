// ============================================
// API Types - All data structures for API responses
// ============================================

// ============================================
// Central API Response Types (서버 응답 타입)
// ============================================

export interface OrderLineOut {
  order_line_id: number;
  order_id: number;
  item_id: number;
  item_name?: string | null;  // 메뉴 아이템 이름
  qty: number;
  unit_price_won: number;
  line_amount_won: number;
}

export interface OrderHdrOut {
  order_id: number;
  store_id: number;
  store_name?: string | null;  // 매장 이름
  session_id: number;
  total_amount_won: number;
  status: string; // PENDING, PAID, CANCELLED 등
  created_at: string;
  lines: OrderLineOut[];
}

export interface ReviewOut {
  review_id: number;
  session_id: number;
  run_id: number | null;
  status: "OPEN" | "RESOLVED";
  reason: string;
  top_k_json: unknown | null;
  confirmed_items_json: unknown | null;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  store_name: string | null;
  device_code: string | null;
}

// CCTV Event Types
export type CctvEventType = "VANDALISM" | "VIOLENCE" | "FALL" | "WHEELCHAIR";
export type CctvEventStatus = "OPEN" | "CONFIRMED" | "DISMISSED";

export interface CctvEventClipOut {
  clip_id: number;
  event_id: number;
  clip_gcs_uri: string;
  clip_signed_url?: string;
  clip_start_at: string;
  clip_end_at: string;
  created_at: string;
}

export interface CctvEventOut {
  event_id: number;
  store_id: number;
  cctv_device_id: number;
  event_type: CctvEventType;
  confidence: number;
  status: CctvEventStatus;
  started_at: string;
  ended_at: string;
  meta_json: unknown | null;
  created_at: string;
  clips: CctvEventClipOut[];
}

// ============================================
// Client Types (클라이언트 타입)
// ============================================

// Dashboard KPI Types
export interface KPIData {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  trend: "up" | "down" | "neutral";
  variant: "revenue" | "customers" | "occupancy" | "alerts";
}

// Transaction Types
export type TransactionStatus = "AUTO" | "REVIEW" | "ERROR";

export interface Transaction {
  id: string;
  device: string;
  product: string;
  amount: string;
  status: TransactionStatus;
  time?: string;
  customer?: string;
}

// Alert Types
export type AlertSeverity = "critical" | "warning" | "normal";
export type AlertCategory = "payment" | "safety" | "security" | "system";

export interface Alert {
  id: string;
  type: AlertSeverity;
  category: AlertCategory;
  message: string;
  location: string;
  timestamp: string;
  isRead: boolean;
  review_id?: number;  // 리뷰 ID (확정 처리에 필요)
  top_k_json?: any;    // AI 인식 결과 (확정 처리에 필요)
  // CCTV 이벤트 관련 필드
  event_id?: number;   // CCTV 이벤트 ID
  clip_url?: string;   // 영상 클립 URL (GCS URI)
  event_type?: CctvEventType;  // CCTV 이벤트 타입
}

export interface AlertSummary {
  id: number;
  severity: AlertSeverity;
  type: string;
  message: string;
  timestamp: string;
}

// Device Types
export type DeviceType = "camera" | "sensor" | "display";
export type DeviceStatus = "online" | "warning" | "offline";

export interface Device {
  id: string;
  name: string;
  type: DeviceType;
  location: string;
  status: DeviceStatus;
  battery?: number;
  lastActive: string;
}

// Store Types
export interface StoreInfo {
  name: string;
  address: string;
  operatingHours: string;
  totalTables: number;
  totalDevices: number;
  onlineDevices: number;
}

// Analytics Types
export interface WeeklyDataPoint {
  day: string;
  revenue: number;
  customers: number;
}

export interface HourlyDataPoint {
  hour: string;
  customers: number;
}

export interface HourlyRevenuePoint {
  time: string;
  revenue: number;
}

export interface CategoryData {
  name: string;
  value: number;
  color: string;
}

export interface ProductSalesData {
  name: string;
  nameEn: string;
  value: number;
  percentage: number;
}

export interface AnalyticsStat {
  label: string;
  value: string;
  change: string;
  trend: "up" | "down";
  iconType: "trending" | "users" | "shopping" | "clock";
}

// Dashboard Summary Types
export interface DashboardSummary {
  kpis: KPIData[];
  transactions: Transaction[];
  alerts: AlertSummary[];
  hourlyRevenue: HourlyRevenuePoint[];
  productSales: ProductSalesData[];
}
