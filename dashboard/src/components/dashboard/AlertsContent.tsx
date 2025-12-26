import { useState, useEffect, useMemo } from "react";
import { Bell, AlertTriangle, CheckCircle, XCircle, Filter, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Alert, AlertSeverity, AlertCategory } from "@/api/types";
import { fetchAlerts } from "@/api/alertsApi";

const AlertsContent = () => {
  const [filter, setFilter] = useState<AlertSeverity | "all">("all");
  const [categoryFilter, setCategoryFilter] = useState<AlertCategory | "all">("all");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const data = await fetchAlerts();
        setAlerts(data);
      } catch (err) {
        console.error("Alerts data fetch error:", err);
        setError(err instanceof Error ? err.message : "데이터를 불러오는데 실패했습니다");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const matchesType = filter === "all" || alert.type === filter;
      const matchesCategory = categoryFilter === "all" || alert.category === categoryFilter;
      return matchesType && matchesCategory;
    });
  }, [alerts, filter, categoryFilter]);

  const stats = useMemo(() => ({
    unread: alerts.filter(a => !a.isRead).length,
    critical: alerts.filter(a => a.type === "critical").length,
  }), [alerts]);

  const getTypeIcon = (type: AlertSeverity) => {
    switch (type) {
      case "critical": return <XCircle className="w-5 h-5 text-destructive" />;
      case "warning": return <AlertTriangle className="w-5 h-5 text-warning" />;
      case "normal": return <CheckCircle className="w-5 h-5 text-success" />;
    }
  };

  const getTypeBadge = (type: AlertSeverity) => {
    const styles: Record<AlertSeverity, string> = {
      critical: "bg-destructive/20 text-destructive",
      warning: "bg-warning/20 text-warning",
      normal: "bg-success/20 text-success",
    };
    return styles[type];
  };

  const getCategoryBadge = (category: AlertCategory) => {
    const labels: Record<AlertCategory, string> = { payment: "결제", safety: "안전", security: "보안" };
    return labels[category];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">알림 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-destructive text-lg mb-2">오류 발생</p>
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Bell className="w-7 h-7 text-primary" />
            알림 센터
          </h2>
          <p className="text-muted-foreground mt-1">Alert Center</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-destructive/20 text-destructive px-3 py-1.5 rounded-lg text-sm font-medium">
            긴급: {stats.critical}
          </div>
          <div className="bg-primary/20 text-primary px-3 py-1.5 rounded-lg text-sm font-medium">
            미확인: {stats.unread}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-2xl p-4 border border-border flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">유형:</span>
          {(["all", "critical", "warning", "normal"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                filter === type
                  ? "bg-primary text-primary-foreground"
                  : "bg-background border border-border text-muted-foreground hover:text-foreground"
              )}
            >
              {type === "all" ? "전체" : type === "critical" ? "긴급" : type === "warning" ? "주의" : "정상"}
            </button>
          ))}
        </div>
        <div className="w-px h-6 bg-border" />
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">카테고리:</span>
          {(["all", "payment", "safety", "security"] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                categoryFilter === cat
                  ? "bg-primary text-primary-foreground"
                  : "bg-background border border-border text-muted-foreground hover:text-foreground"
              )}
            >
              {cat === "all" ? "전체" : cat === "payment" ? "결제" : cat === "safety" ? "안전" : "보안"}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            알림이 없습니다
          </div>
        ) : filteredAlerts.map((alert, index) => (
          <div
            key={alert.id}
            className={cn(
              "bg-card rounded-xl p-4 border border-border transition-all hover:shadow-lg",
              !alert.isRead && "ring-1 ring-primary/50 bg-primary/5",
              alert.type === "critical" && "border-destructive/50"
            )}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start gap-4">
              <div className={cn(
                "p-2 rounded-lg",
                alert.type === "critical" && "bg-destructive/20",
                alert.type === "warning" && "bg-warning/20",
                alert.type === "normal" && "bg-success/20"
              )}>
                {getTypeIcon(alert.type)}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn(
                    "px-2 py-0.5 rounded-full text-xs font-medium",
                    getTypeBadge(alert.type)
                  )}>
                    {alert.type === "critical" ? "긴급" : alert.type === "warning" ? "주의" : "정상"}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                    {getCategoryBadge(alert.category)}
                  </span>
                  {!alert.isRead && (
                    <span className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                  )}
                </div>
                <p className="text-foreground font-medium">{alert.message}</p>
                <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                  <span>📍 {alert.location}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {alert.timestamp}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {alert.type === "critical" && (
                  <button className="px-3 py-1.5 bg-destructive text-destructive-foreground rounded-lg text-sm font-medium hover:bg-destructive/90 transition-colors">
                    확인
                  </button>
                )}
                {alert.type === "warning" && (
                  <button className="px-3 py-1.5 bg-warning/20 text-warning rounded-lg text-sm font-medium hover:bg-warning/30 transition-colors">
                    처리
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsContent;
