import { Store, Camera, Wifi, Battery, CheckCircle, AlertTriangle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Device, DeviceType, DeviceStatus, StoreInfo } from "@/api/types";
import { mockDevices, mockStoreInfo } from "@/api/mockData";

const StoreContent = () => {
  // Data from API layer
  const devices: Device[] = mockDevices;
  const storeInfo: StoreInfo = mockStoreInfo;

  const getStatusIcon = (status: DeviceStatus) => {
    switch (status) {
      case "online": return <CheckCircle className="w-4 h-4 text-success" />;
      case "warning": return <AlertTriangle className="w-4 h-4 text-warning" />;
      case "offline": return <XCircle className="w-4 h-4 text-destructive" />;
    }
  };

  const getStatusBadge = (status: DeviceStatus) => {
    const styles: Record<DeviceStatus, string> = {
      online: "bg-success/20 text-success",
      warning: "bg-warning/20 text-warning",
      offline: "bg-destructive/20 text-destructive",
    };
    return styles[status];
  };

  const getDeviceIcon = (type: DeviceType) => {
    switch (type) {
      case "camera": return <Camera className="w-5 h-5" />;
      case "sensor": return <Wifi className="w-5 h-5" />;
      case "display": return <Store className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Store className="w-7 h-7 text-primary" />
          매장 관리
        </h2>
        <p className="text-muted-foreground mt-1">Store Management</p>
      </div>

      {/* Store Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">매장 정보</h3>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">매장명</p>
              <p className="text-foreground font-medium">{storeInfo.name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">주소</p>
              <p className="text-foreground font-medium">{storeInfo.address}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">영업 시간</p>
              <p className="text-foreground font-medium">{storeInfo.operatingHours}</p>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">테이블 현황</h3>
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <p className="text-5xl font-bold text-primary">{storeInfo.totalTables}</p>
              <p className="text-muted-foreground mt-2">총 테이블 수</p>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">디바이스 상태</h3>
          <div className="flex items-center justify-between h-32">
            <div className="text-center flex-1">
              <p className="text-4xl font-bold text-success">{storeInfo.onlineDevices}</p>
              <p className="text-muted-foreground mt-2">온라인</p>
            </div>
            <div className="w-px h-16 bg-border" />
            <div className="text-center flex-1">
              <p className="text-4xl font-bold text-destructive">{storeInfo.totalDevices - storeInfo.onlineDevices}</p>
              <p className="text-muted-foreground mt-2">오프라인</p>
            </div>
          </div>
        </div>
      </div>

      {/* Devices Grid */}
      <div className="bg-card rounded-2xl border border-border p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">디바이스 목록</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {devices.map((device) => (
            <div
              key={device.id}
              className={cn(
                "p-4 rounded-xl border transition-all hover:shadow-lg",
                device.status === "online" && "bg-success/5 border-success/30",
                device.status === "warning" && "bg-warning/5 border-warning/30",
                device.status === "offline" && "bg-destructive/5 border-destructive/30"
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={cn(
                  "p-2 rounded-lg",
                  device.status === "online" && "bg-success/20 text-success",
                  device.status === "warning" && "bg-warning/20 text-warning",
                  device.status === "offline" && "bg-destructive/20 text-destructive"
                )}>
                  {getDeviceIcon(device.type)}
                </div>
                <span className={cn(
                  "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
                  getStatusBadge(device.status)
                )}>
                  {getStatusIcon(device.status)}
                  {device.status === "online" ? "온라인" : device.status === "warning" ? "주의" : "오프라인"}
                </span>
              </div>
              <h4 className="font-medium text-foreground">{device.name}</h4>
              <p className="text-sm text-muted-foreground mt-1">{device.location}</p>
              <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
                <span>{device.id}</span>
                {device.battery !== undefined && (
                  <span className="flex items-center gap-1">
                    <Battery className={cn(
                      "w-3 h-3",
                      device.battery > 50 ? "text-success" : device.battery > 20 ? "text-warning" : "text-destructive"
                    )} />
                    {device.battery}%
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2">마지막 활동: {device.lastActive}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StoreContent;
