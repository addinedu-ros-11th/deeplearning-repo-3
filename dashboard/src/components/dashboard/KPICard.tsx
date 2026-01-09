import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import type { KPIData } from "@/api/types";

type KPIVariant = KPIData["variant"];
type KPITrend = KPIData["trend"];

interface KPICardProps {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  trend?: KPITrend;
  variant: KPIVariant;
  delay?: number;
}

const variantStyles: Record<KPIVariant, string> = {
  revenue: "from-kpi-revenue/30 to-kpi-revenue/10 border-kpi-revenue/30",
  customers: "from-kpi-customers/30 to-kpi-customers/10 border-kpi-customers/30",
  occupancy: "from-kpi-occupancy/30 to-kpi-occupancy/10 border-kpi-occupancy/30",
  alerts: "from-kpi-alerts/30 to-kpi-alerts/10 border-kpi-alerts/30",
};

const iconVariantStyles: Record<KPIVariant, string> = {
  revenue: "bg-kpi-revenue/20 text-kpi-revenue",
  customers: "bg-kpi-customers/20 text-kpi-customers",
  occupancy: "bg-kpi-occupancy/20 text-kpi-occupancy",
  alerts: "bg-kpi-alerts/20 text-kpi-alerts",
};

const KPICard = ({ icon, title, value, subtitle, trend = "neutral", variant, delay = 0 }: KPICardProps) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border p-6",
        "bg-gradient-to-br backdrop-blur-sm",
        "hover-lift cursor-default",
        variantStyles[variant],
        isVisible ? "animate-fade-in-up" : "opacity-0"
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Background glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-primary/5" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center text-2xl", iconVariantStyles[variant])}>
            {icon}
          </div>
          {trend === "up" && (
            <span className="text-success text-sm font-medium">↑</span>
          )}
          {trend === "down" && (
            <span className="text-destructive text-sm font-medium">↓</span>
          )}
        </div>
        
        <p className="text-sm text-muted-foreground mb-1">{title}</p>
        <p className="text-2xl font-bold text-foreground mb-2 animate-count-up">{value}</p>
        <p className={cn(
          "text-sm",
          trend === "up" && "text-success",
          trend === "down" && "text-destructive",
          trend === "neutral" && "text-muted-foreground"
        )}>
          {subtitle}
        </p>
      </div>
    </div>
  );
};

export default KPICard;
