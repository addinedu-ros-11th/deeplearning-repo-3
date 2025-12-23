// ============================================
// Mock Data - Placeholder data for development
// Replace with real API responses later
// ============================================

import type {
  KPIData,
  Transaction,
  TableData,
  Alert,
  AlertSummary,
  Device,
  StoreInfo,
  WeeklyDataPoint,
  HourlyDataPoint,
  HourlyRevenuePoint,
  CategoryData,
  ProductSalesData,
  AnalyticsStat,
} from "./types";

// Dashboard KPIs
export const mockKPIs: KPIData[] = [
  {
    icon: "📈",
    title: "Real-time Revenue",
    value: "₩2,450,000",
    subtitle: "↑ +12.5% 어제 대비",
    trend: "up",
    variant: "revenue",
  },
  {
    icon: "👥",
    title: "Current Customers",
    value: "28명",
    subtitle: "8/10 테이블 사용중",
    trend: "neutral",
    variant: "customers",
  },
  {
    icon: "🪑",
    title: "Table Occupancy",
    value: "80%",
    subtitle: "8개 테이블 점유",
    trend: "up",
    variant: "occupancy",
  },
  {
    icon: "🚨",
    title: "Pending Alerts",
    value: "3건",
    subtitle: "1건 긴급",
    trend: "down",
    variant: "alerts",
  },
];

// Transactions for TransactionLog component
export const mockTransactionsShort: Transaction[] = [
  { id: "TXN001", device: "01", product: "크루아상", amount: "₩5,000", status: "AUTO" },
  { id: "TXN002", device: "02", product: "식빵+크림", amount: "₩15,000", status: "REVIEW" },
  { id: "TXN003", device: "01", product: "베이글", amount: "₩4,000", status: "AUTO" },
  { id: "TXN004", device: "03", product: "초코칩 쿠키", amount: "₩6,500", status: "AUTO" },
  { id: "TXN005", device: "02", product: "도넛 세트", amount: "₩12,000", status: "AUTO" },
  { id: "TXN006", device: "01", product: "식빵", amount: "₩8,000", status: "AUTO" },
  { id: "TXN007", device: "03", product: "크루아상 x2", amount: "₩10,000", status: "AUTO" },
  { id: "TXN008", device: "02", product: "베이글+버터", amount: "₩9,000", status: "REVIEW" },
];

// Extended Transactions for PaymentContent
export const mockTransactionsFull: Transaction[] = [
  { id: "TXN001", device: "01", product: "크로와상", amount: "₩5,000", status: "AUTO", time: "14:32", customer: "Table 3" },
  { id: "TXN002", device: "02", product: "식빵+크림치즈", amount: "₩15,000", status: "REVIEW", time: "14:28", customer: "Table 5" },
  { id: "TXN003", device: "01", product: "베이글", amount: "₩4,000", status: "AUTO", time: "14:25", customer: "Table 1" },
  { id: "TXN004", device: "03", product: "초코칩 쿠키", amount: "₩6,500", status: "AUTO", time: "14:20", customer: "Table 7" },
  { id: "TXN005", device: "02", product: "도넛 세트", amount: "₩12,000", status: "AUTO", time: "14:15", customer: "Table 2" },
  { id: "TXN006", device: "01", product: "식빵", amount: "₩8,000", status: "ERROR", time: "14:10", customer: "Table 4" },
  { id: "TXN007", device: "03", product: "크로와상 x2", amount: "₩10,000", status: "AUTO", time: "14:05", customer: "Table 6" },
  { id: "TXN008", device: "02", product: "베이글+버터", amount: "₩9,000", status: "REVIEW", time: "14:00", customer: "Table 8" },
  { id: "TXN009", device: "01", product: "치즈케이크", amount: "₩7,500", status: "AUTO", time: "13:55", customer: "Table 9" },
  { id: "TXN010", device: "03", product: "아메리카노", amount: "₩4,500", status: "AUTO", time: "13:50", customer: "Table 10" },
];

// Table Floor Plan
export const mockTables: TableData[] = [
  { id: 1, status: "occupied", customers: 3, occupancyTime: "45분", orderAmount: "₩35,000" },
  { id: 2, status: "occupied", customers: 2, occupancyTime: "20분", orderAmount: "₩22,000" },
  { id: 3, status: "abnormal", customers: 4, occupancyTime: "1시간 12분", orderAmount: "₩48,000" },
  { id: 4, status: "vacant" },
  { id: 5, status: "cleaning", occupancyTime: "청소 대기" },
  { id: 6, status: "occupied", customers: 1, occupancyTime: "15분", orderAmount: "₩8,500" },
  { id: 7, status: "abnormal", customers: 2, occupancyTime: "55분", orderAmount: "₩41,000" },
  { id: 8, status: "occupied", customers: 5, occupancyTime: "35분", orderAmount: "₩62,000" },
  { id: 9, status: "vacant" },
  { id: 10, status: "occupied", customers: 2, occupancyTime: "28분", orderAmount: "₩19,500" },
];

// Alerts for AlertsList
export const mockAlertsSummary: AlertSummary[] = [
  { id: 1, severity: "critical", type: "안전", message: "테이블 3 - 고객 낙상 감지됨", timestamp: "14:32" },
  { id: 2, severity: "warning", type: "청소", message: "테이블 5 - 청소 필요", timestamp: "14:28" },
  { id: 3, severity: "normal", type: "결제", message: "기기 2 - REVIEW 거래 승인됨", timestamp: "14:25" },
  { id: 4, severity: "critical", type: "보안", message: "테이블 7 - 이상 행동 감지됨", timestamp: "14:20" },
  { id: 5, severity: "warning", type: "결제", message: "기기 1 - 낮은 신뢰도 거래", timestamp: "14:15" },
  { id: 6, severity: "normal", type: "매장", message: "테이블 1 - 입석 시작됨", timestamp: "14:10" },
];

// Alerts for AlertsContent (full detail)
export const mockAlertsFull: Alert[] = [
  { id: "ALT001", type: "critical", category: "safety", message: "테이블 3번 고객 낙상 감지", location: "테이블 3", timestamp: "14:32", isRead: false },
  { id: "ALT002", type: "warning", category: "payment", message: "저신뢰도 거래 발생", location: "Device 2", timestamp: "14:28", isRead: false },
  { id: "ALT003", type: "warning", category: "security", message: "테이블 5 청소 필요", location: "테이블 5", timestamp: "14:25", isRead: true },
  { id: "ALT004", type: "normal", category: "payment", message: "REVIEW 거래 승인 완료", location: "Device 2", timestamp: "14:20", isRead: true },
  { id: "ALT005", type: "critical", category: "security", message: "비정상 행동 감지", location: "테이블 7", timestamp: "14:15", isRead: false },
  { id: "ALT006", type: "warning", category: "payment", message: "Device 1 저신뢰도 거래", location: "Device 1", timestamp: "14:10", isRead: true },
  { id: "ALT007", type: "normal", category: "safety", message: "테이블 1 점유 시작", location: "테이블 1", timestamp: "14:05", isRead: true },
  { id: "ALT008", type: "warning", category: "security", message: "카메라 연결 불안정", location: "CAM-03", timestamp: "14:00", isRead: false },
  { id: "ALT009", type: "normal", category: "payment", message: "일괄 정산 완료", location: "시스템", timestamp: "13:55", isRead: true },
  { id: "ALT010", type: "critical", category: "safety", message: "긴급 버튼 호출", location: "테이블 9", timestamp: "13:50", isRead: true },
];

// Devices
export const mockDevices: Device[] = [
  { id: "CAM-01", name: "입구 카메라", type: "camera", location: "입구", status: "online", lastActive: "방금 전" },
  { id: "CAM-02", name: "테이블존 카메라 1", type: "camera", location: "테이블 1-5", status: "online", lastActive: "방금 전" },
  { id: "CAM-03", name: "테이블존 카메라 2", type: "camera", location: "테이블 6-10", status: "warning", lastActive: "5분 전" },
  { id: "CAM-04", name: "결제구역 카메라", type: "camera", location: "결제 구역", status: "online", lastActive: "방금 전" },
  { id: "SEN-01", name: "테이블 1 센서", type: "sensor", location: "테이블 1", status: "online", battery: 85, lastActive: "방금 전" },
  { id: "SEN-02", name: "테이블 2 센서", type: "sensor", location: "테이블 2", status: "online", battery: 72, lastActive: "방금 전" },
  { id: "SEN-03", name: "테이블 3 센서", type: "sensor", location: "테이블 3", status: "offline", battery: 15, lastActive: "2시간 전" },
  { id: "DIS-01", name: "메인 디스플레이", type: "display", location: "입구", status: "online", lastActive: "방금 전" },
];

// Store Info
export const mockStoreInfo: StoreInfo = {
  name: "Bake Sight 강남점",
  address: "서울시 강남구 테헤란로 123",
  operatingHours: "09:00 - 22:00",
  totalTables: 10,
  totalDevices: 8,
  onlineDevices: 6,
};

// Hourly Revenue Chart
export const mockHourlyRevenue: HourlyRevenuePoint[] = [
  { time: "09:00", revenue: 150000 },
  { time: "10:00", revenue: 280000 },
  { time: "11:00", revenue: 420000 },
  { time: "12:00", revenue: 580000 },
  { time: "13:00", revenue: 380000 },
  { time: "14:00", revenue: 220000 },
  { time: "15:00", revenue: 320000 },
  { time: "16:00", revenue: 450000 },
  { time: "17:00", revenue: 560000 },
  { time: "18:00", revenue: 640000 },
  { time: "19:00", revenue: 620000 },
  { time: "20:00", revenue: 480000 },
  { time: "21:00", revenue: 240000 },
];

// Product Sales
export const mockProductSales: ProductSalesData[] = [
  { name: "크루아상", nameEn: "Croissant", value: 45, percentage: 25 },
  { name: "식빵", nameEn: "Bread Loaf", value: 38, percentage: 20 },
  { name: "초코칩 쿠키", nameEn: "Choco Chip Cookie", value: 32, percentage: 18 },
  { name: "베이글", nameEn: "Bagel", value: 28, percentage: 15 },
  { name: "도넛", nameEn: "Donut", value: 22, percentage: 12 },
  { name: "기타", nameEn: "Others", value: 15, percentage: 10 },
];

// Analytics Weekly Data
export const mockWeeklyData: WeeklyDataPoint[] = [
  { day: "월", revenue: 2100000, customers: 145 },
  { day: "화", revenue: 1850000, customers: 128 },
  { day: "수", revenue: 2300000, customers: 162 },
  { day: "목", revenue: 2450000, customers: 175 },
  { day: "금", revenue: 2800000, customers: 198 },
  { day: "토", revenue: 3200000, customers: 225 },
  { day: "일", revenue: 2900000, customers: 205 },
];

// Analytics Hourly Customers
export const mockHourlyCustomers: HourlyDataPoint[] = [
  { hour: "09", customers: 12 },
  { hour: "10", customers: 25 },
  { hour: "11", customers: 38 },
  { hour: "12", customers: 65 },
  { hour: "13", customers: 52 },
  { hour: "14", customers: 35 },
  { hour: "15", customers: 42 },
  { hour: "16", customers: 55 },
  { hour: "17", customers: 68 },
  { hour: "18", customers: 72 },
  { hour: "19", customers: 58 },
  { hour: "20", customers: 45 },
  { hour: "21", customers: 28 },
];

// Analytics Category Data
export const mockCategoryData: CategoryData[] = [
  { name: "빵류", value: 45, color: "hsl(var(--primary))" },
  { name: "음료", value: 25, color: "hsl(var(--accent))" },
  { name: "케이크", value: 15, color: "hsl(var(--secondary))" },
  { name: "쿠키", value: 10, color: "hsl(var(--warning))" },
  { name: "기타", value: 5, color: "hsl(var(--muted-foreground))" },
];

// Analytics Stats
export const mockAnalyticsStats: AnalyticsStat[] = [
  { label: "주간 총 매출", value: "₩17,600,000", change: "+12.5%", trend: "up", iconType: "trending" },
  { label: "주간 방문객", value: "1,238명", change: "+8.2%", trend: "up", iconType: "users" },
  { label: "평균 객단가", value: "₩14,200", change: "-2.1%", trend: "down", iconType: "shopping" },
  { label: "평균 체류시간", value: "32분", change: "+5.3%", trend: "up", iconType: "clock" },
];
