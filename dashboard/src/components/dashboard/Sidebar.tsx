import { useState } from "react";
import {
  Home,
  CreditCard,
  Store,
  BarChart3,
  Bell,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  icon: React.ElementType;
  label: string;
  labelKr: string;
  id: string;
}

const navItems: NavItem[] = [
  { icon: Home, label: "Dashboard", labelKr: "대시보드", id: "dashboard" },
  { icon: CreditCard, label: "Payment", labelKr: "결제 관리", id: "payment" },
  { icon: Store, label: "Store", labelKr: "매장 관리", id: "store" },
  { icon: BarChart3, label: "Analytics", labelKr: "분석", id: "analytics" },
  { icon: Bell, label: "Alerts", labelKr: "알림", id: "alerts" },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (id: string) => void;
}

const Sidebar = ({ activeTab, onTabChange }: SidebarProps) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300 ease-out",
        collapsed ? "w-20" : "w-64"
      )}
    >
      {/* Logo Section */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow">
            <span className="text-xl">🍞</span>
          </div>
          {!collapsed && (
            <div className="animate-fade-in">
              <h1 className="text-lg font-bold text-foreground">Bake Sight</h1>
              <p className="text-xs text-muted-foreground">by 빵끗</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200",
                "hover:bg-sidebar-accent group",
                isActive 
                  ? "bg-primary/20 text-primary shadow-glow" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon 
                className={cn(
                  "w-5 h-5 transition-transform duration-200",
                  "group-hover:scale-110",
                  isActive && "text-primary"
                )} 
              />
              {!collapsed && (
                <div className="flex flex-col items-start animate-fade-in">
                  <span className="text-sm font-medium">{item.label}</span>
                  <span className="text-xs text-muted-foreground">{item.labelKr}</span>
                </div>
              )}
              {isActive && !collapsed && (
                <div className="ml-auto w-1.5 h-6 bg-primary rounded-full" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-4 border-t border-sidebar-border">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-sidebar-accent text-muted-foreground hover:text-foreground transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
