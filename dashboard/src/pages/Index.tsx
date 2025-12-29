import { useState } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import Header from "@/components/dashboard/Header";
import DashboardContent from "@/components/dashboard/DashboardContent";
import PaymentContent from "@/components/dashboard/PaymentContent";
import StoreContent from "@/components/dashboard/StoreContent";
import AnalyticsContent from "@/components/dashboard/AnalyticsContent";
import AlertsContent from "@/components/dashboard/AlertsContent";

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return <DashboardContent />;
      case "payment":
        return <PaymentContent />;
      case "store":
        return <StoreContent />;
      case "analytics":
        return <AnalyticsContent />;
      case "alerts":
        return <AlertsContent />;
      default:
        return <DashboardContent />;
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

        {/* Dynamic Content */}
        <main className="flex-1 overflow-auto p-6 scrollbar-thin">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

export default Index;
