import KPICard from "./KPICard";
import TableFloorPlan from "./TableFloorPlan";
import HourlyRevenueChart from "./HourlyRevenueChart";
import ProductSalesChart from "./ProductSalesChart";
import TransactionLog from "./TransactionLog";
import AlertsList from "./AlertsList";
import { mockKPIs } from "@/api/mockData";

const DashboardContent = () => {
  // Data is now consumed from the API layer through props or direct imports
  const kpis = mockKPIs;

  return (
    <>
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {kpis.map((kpi, index) => (
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
        ))}
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-6">
        {/* Left Column - 40% */}
        <div className="lg:col-span-4 space-y-6">
          <TableFloorPlan />
          <TransactionLog />
        </div>

        {/* Right Column - 60% */}
        <div className="lg:col-span-6 space-y-6">
          <HourlyRevenueChart />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ProductSalesChart />
            <AlertsList />
          </div>
        </div>
      </div>
    </>
  );
};

export default DashboardContent;
