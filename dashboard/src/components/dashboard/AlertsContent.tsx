import { useState, useEffect, useMemo } from "react";
import { Bell, AlertTriangle, CheckCircle, XCircle, Filter, Clock, Video, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Alert, AlertSeverity, AlertCategory } from "@/api/types";
import { fetchAlerts, confirmReview } from "@/api/alertsApi";

const AlertsContent = () => {
  const [filter, setFilter] = useState<AlertSeverity | "all">("all");
  const [categoryFilter, setCategoryFilter] = useState<AlertCategory | "all">("all");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null); // 영상 모달용

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

  const handleConfirm = async (alertItem: Alert) => {
    console.log("handleConfirm 호출:", alertItem);
    console.log("review_id:", alertItem.review_id);
    console.log("top_k_json:", alertItem.top_k_json);

    if (!alertItem.review_id) {
      console.error("리뷰 확정 처리 실패: review_id가 없습니다");
      window.alert("리뷰 확정 처리 실패: review_id가 없습니다.");
      return;
    }

    // top_k_json 검증 - 배열이고 비어있지 않아야 함
    if (!Array.isArray(alertItem.top_k_json) || alertItem.top_k_json.length === 0) {
      console.error("리뷰 확정 처리 실패: top_k_json이 비어있습니다", alertItem.top_k_json);
      window.alert("리뷰 확정 처리 실패: 인식된 아이템이 없습니다.");
      return;
    }

    try {
      await confirmReview(alertItem.review_id, alertItem.top_k_json);
      // 알림 목록 새로고침
      const data = await fetchAlerts();
      setAlerts(data);
      window.alert("리뷰가 확정 처리되었습니다.");
    } catch (err) {
      console.error("리뷰 확정 처리 오류:", err);
      const errorMsg = err instanceof Error ? err.message : "알 수 없는 오류";
      window.alert(`리뷰 확정 처리에 실패했습니다: ${errorMsg}`);
    }
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
                {/* 영상 버튼 - 긴급/주의 알림 중 clip_url이 있는 경우만 표시 */}
                {(alert.type === "critical" || alert.type === "warning") && alert.clip_url && (
                  <button
                    onClick={() => setSelectedVideo(alert.clip_url!)}
                    className="px-3 py-1.5 bg-primary/20 text-primary rounded-lg text-sm font-medium hover:bg-primary/30 transition-colors flex items-center gap-1"
                  >
                    <Video className="w-4 h-4" />
                    영상
                  </button>
                )}
                {alert.type === "critical" && (
                  <button
                    onClick={() => handleConfirm(alert)}
                    className="px-3 py-1.5 bg-destructive text-destructive-foreground rounded-lg text-sm font-medium hover:bg-destructive/90 transition-colors"
                  >
                    확인
                  </button>
                )}
                {alert.type === "warning" && (
                  <button
                    onClick={() => handleConfirm(alert)}
                    className="px-3 py-1.5 bg-warning/20 text-warning rounded-lg text-sm font-medium hover:bg-warning/30 transition-colors"
                  >
                    처리
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 영상 모달 */}
      {selectedVideo && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
          onClick={() => setSelectedVideo(null)}
        >
          <div
            className="bg-card rounded-2xl p-4 max-w-4xl w-full mx-4 relative"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedVideo(null)}
              className="absolute top-4 right-4 p-2 bg-muted rounded-full hover:bg-muted/80 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Video className="w-5 h-5 text-primary" />
              CCTV 영상
            </h3>
            <div className="aspect-video bg-black rounded-lg overflow-hidden">
              <video
                src={selectedVideo}
                controls
                autoPlay
                className="w-full h-full object-contain"
              >
                브라우저가 비디오를 지원하지 않습니다.
              </video>
            </div>
            <p className="text-sm text-muted-foreground mt-2 break-all">
              {selectedVideo}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsContent;
