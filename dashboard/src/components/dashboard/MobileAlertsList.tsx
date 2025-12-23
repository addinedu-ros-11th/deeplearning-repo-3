import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ChevronRight } from "lucide-react";

interface Alert {
  id: number;
  severity: "critical" | "warning" | "normal";
  type: string;
  message: string;
  timestamp: string;
}

const alerts: Alert[] = [
  { id: 1, severity: "critical", type: "안전", message: "테이블 3 - 고객 낙상 감지됨", timestamp: "14:32" },
  { id: 2, severity: "warning", type: "청소", message: "테이블 5 - 청소 필요", timestamp: "14:28" },
  { id: 3, severity: "normal", type: "결제", message: "기기 2 - REVIEW 거래 승인됨", timestamp: "14:25" },
  { id: 4, severity: "critical", type: "보안", message: "테이블 7 - 이상 행동 감지됨", timestamp: "14:20" },
];

const severityConfig = {
  critical: {
    icon: "🚨",
    bg: "bg-destructive/10 border-l-destructive",
    badge: "bg-destructive/20 text-destructive border-destructive/30",
  },
  warning: {
    icon: "⚠️",
    bg: "bg-warning/10 border-l-warning",
    badge: "bg-warning/20 text-warning border-warning/30",
  },
  normal: {
    icon: "✅",
    bg: "bg-success/5 border-l-success",
    badge: "bg-success/20 text-success border-success/30",
  },
};

const MobileAlertsList = () => {
  const criticalCount = alerts.filter(a => a.severity === "critical").length;

  return (
    <div className="rounded-2xl border border-border bg-card overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-lg">🔔</span>
          <div>
            <h3 className="text-base font-semibold text-foreground">실시간 알림</h3>
            <span className="text-xs text-muted-foreground">Real-time Alerts</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {criticalCount > 0 && (
            <Badge variant="outline" className="bg-destructive/20 text-destructive border-destructive/30 text-xs">
              {criticalCount} 긴급
            </Badge>
          )}
          <button className="text-xs text-primary font-medium flex items-center gap-1">
            전체 <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      <div className="divide-y divide-border">
        {alerts.map((alert) => {
          const config = severityConfig[alert.severity];
          return (
            <button
              key={alert.id}
              className={cn(
                "w-full p-4 flex items-start gap-3 text-left border-l-4",
                "active:bg-muted/30 transition-colors touch-manipulation",
                config.bg
              )}
            >
              <span className="text-xl flex-shrink-0">{config.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className={cn("text-[10px] px-1.5 py-0", config.badge)}>
                    {alert.type}
                  </Badge>
                </div>
                <p className="text-sm text-foreground">{alert.message}</p>
              </div>
              <span className="text-xs text-muted-foreground flex-shrink-0">{alert.timestamp}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default MobileAlertsList;
