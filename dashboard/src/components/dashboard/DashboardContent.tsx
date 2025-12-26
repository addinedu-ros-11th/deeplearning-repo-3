import { useState, useEffect } from "react";
import KPICard from "./KPICard";
import TableFloorPlan from "./TableFloorPlan";
import HourlyRevenueChart from "./HourlyRevenueChart";
import ProductSalesChart from "./ProductSalesChart";
import TransactionLog from "./TransactionLog";
import AlertsList from "./AlertsList";
import {
  fetchKPIs,
  fetchRecentTransactions,
  fetchAlertsSummary,
  fetchProductSales,
  fetchTables,
  fetchHourlyRevenue,
} from "@/api/dashboardApi";
import type {
  KPIData,
  Transaction,
  AlertSummary,
  ProductSalesData,
  TableData,
  HourlyRevenuePoint,
} from "@/api/types";

interface DashboardData {
  kpis: KPIData[];
  transactions: Transaction[];
  alerts: AlertSummary[];
  productSales: ProductSalesData[];
  tables: TableData[];
  hourlyRevenue: HourlyRevenuePoint[];
}

const DashboardContent = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [kpis, transactions, alerts, productSales, tables, hourlyRevenue] = await Promise.all([
          fetchKPIs(),
          fetchRecentTransactions(),
          fetchAlertsSummary(),
          fetchProductSales(),
          fetchTables(),
          fetchHourlyRevenue(),
        ]);

        setData({ kpis, transactions, alerts, productSales, tables, hourlyRevenue });
      } catch (err) {
        console.error("Dashboard data fetch error:", err);
        setError(err instanceof Error ? err.message : "데이터를 불러오는데 실패했습니다");
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-destructive text-lg mb-2">⚠️ 오류 발생</p>
          <p className="text-muted-foreground">{error}</p>
          <p className="text-sm text-muted-foreground mt-2">서버가 실행 중인지 확인해주세요</p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {data?.kpis && data.kpis.length > 0 ? (
          data.kpis.map((kpi, index) => (
            <KPICard
              key={kpi.title}
              icon={kpi.icon}
              title={kpi.title}
              value={kpi.value}
              subtitle={kpi.subtitle}
              trend={kpi.trend}
              variant={kpi.variant}
              delay={index * 100}
            />
          ))
        ) : (
          <div className="col-span-4 text-center py-8 text-muted-foreground">
            KPI 데이터 없음
          </div>
        )}
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
        {/* Left Column - 40% */}
        <div className="lg:col-span-4 space-y-6">
          <TableFloorPlan tables={data?.tables} />
          <TransactionLog transactions={data?.transactions} />
        </div>

        {/* Right Column - 60% */}
        <div className="lg:col-span-6 space-y-6">
          <HourlyRevenueChart data={data?.hourlyRevenue} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ProductSalesChart data={data?.productSales} />
            <AlertsList alerts={data?.alerts} />
          </div>
        </div>
      </div>
    </>
  );
};

export default DashboardContent;
