// ============================================
// API Types - All data structures for API responses
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

// Table/Floor Plan Types
export type TableStatus = "occupied" | "cleaning" | "abnormal" | "vacant";

export interface TableData {
  id: number;
  status: TableStatus;
  customers?: number;
  occupancyTime?: string;
  orderAmount?: string;
}

// Alert Types
export type AlertSeverity = "critical" | "warning" | "normal";
export type AlertCategory = "payment" | "safety" | "security";

export interface Alert {
  id: string;
  type: AlertSeverity;
  category: AlertCategory;
  message: string;
  location: string;
  timestamp: string;
  isRead: boolean;
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
  tables: TableData[];
  transactions: Transaction[];
  alerts: AlertSummary[];
  hourlyRevenue: HourlyRevenuePoint[];
  productSales: ProductSalesData[];
}
