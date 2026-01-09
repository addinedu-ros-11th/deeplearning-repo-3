import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { AlertSummary, AlertSeverity } from "@/api/types";

const severityConfig: Record<AlertSeverity, {
  icon: string;
  badge: string;
  bg: string;
  label: string;
}> = {
  critical: {
    icon: "🚨",
    badge: "bg-destructive/20 text-destructive border-destructive/30",
    bg: "bg-destructive/10 border-l-destructive",
    label: "Critical"
  },
  warning: {
    icon: "⚠️",
    badge: "bg-warning/20 text-warning border-warning/30",
    bg: "bg-warning/10 border-l-warning",
    label: "Warning"
  },
  normal: {
    icon: "✅",
    badge: "bg-success/20 text-success border-success/30",
    bg: "bg-success/5 border-l-success",
    label: "Normal"
  },
};

interface AlertsListProps {
  alerts?: AlertSummary[];
}

const AlertsList = ({ alerts = [] }: AlertsListProps) => {
  const criticalCount = alerts.filter(a => a.severity === "critical").length;
  const warningCount = alerts.filter(a => a.severity === "warning").length;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">🔔</span>
          <h3 className="text-lg font-semibold text-foreground">Real-time Alerts</h3>
          <span className="text-sm text-muted-foreground ml-2">실시간 알림</span>
        </div>
        <div className="flex gap-2">
          {criticalCount > 0 && (
            <Badge variant="outline" className="bg-destructive/20 text-destructive border-destructive/30">
              {criticalCount} 긴급
            </Badge>
          )}
          {warningCount > 0 && (
            <Badge variant="outline" className="bg-warning/20 text-warning border-warning/30">
              {warningCount} 주의
            </Badge>
          )}
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          알림이 없습니다
        </div>
      ) : (
        <>
          {/* Alert List */}
          <div className="flex-1 overflow-auto scrollbar-thin space-y-3">
            {alerts.map((alert, index) => {
              const config = severityConfig[alert.severity];
              return (
                <div
                  key={alert.id}
                  className={cn(
                    "p-4 rounded-xl border-l-4 transition-all duration-200 hover:translate-x-1 cursor-pointer",
                    config.bg
                  )}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{config.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className={cn("text-xs", config.badge)}>
                          {config.label}
                        </Badge>
                        <Badge variant="outline" className="text-xs bg-muted/50 text-muted-foreground border-border">
                          {alert.type}
                        </Badge>
                      </div>
                      <p className="text-sm text-foreground">{alert.message}</p>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">{alert.timestamp}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Summary */}
          <div className="mt-4 pt-4 border-t border-border">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">오늘 총 알림</span>
              <span className="text-foreground font-medium">{alerts.length}건</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AlertsList;
