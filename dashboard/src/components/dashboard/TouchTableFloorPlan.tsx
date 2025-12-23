import { cn } from "@/lib/utils";
import { useState } from "react";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface TableData {
  id: number;
  status: "occupied" | "cleaning" | "abnormal" | "vacant";
  customers?: number;
  occupancyTime?: string;
  orderAmount?: string;
}

const tables: TableData[] = [
  { id: 1, status: "occupied", customers: 3, occupancyTime: "45분", orderAmount: "₩35,000" },
  { id: 2, status: "occupied", customers: 2, occupancyTime: "20분", orderAmount: "₩22,000" },
  { id: 3, status: "abnormal", customers: 4, occupancyTime: "1시간 12분", orderAmount: "₩48,000" },
  { id: 4, status: "vacant" },
  { id: 5, status: "cleaning", occupancyTime: "청소 대기" },
  { id: 6, status: "occupied", customers: 1, occupancyTime: "15분", orderAmount: "₩8,500" },
  { id: 7, status: "abnormal", customers: 2, occupancyTime: "55분", orderAmount: "₩41,000" },
  { id: 8, status: "occupied", customers: 5, occupancyTime: "35분", orderAmount: "₩62,000" },
  { id: 9, status: "vacant" },
  { id: 10, status: "occupied", customers: 2, occupancyTime: "28분", orderAmount: "₩19,500" },
];

const statusConfig = {
  occupied: {
    bg: "bg-table-occupied/20 border-table-occupied/50 active:bg-table-occupied/40",
    dot: "bg-table-occupied",
    label: "사용중",
    labelEn: "Occupied"
  },
  cleaning: {
    bg: "bg-table-cleaning/20 border-table-cleaning/50 active:bg-table-cleaning/40",
    dot: "bg-table-cleaning",
    label: "청소 필요",
    labelEn: "Needs Cleaning"
  },
  abnormal: {
    bg: "bg-table-abnormal/20 border-table-abnormal/50 active:bg-table-abnormal/40 animate-pulse-soft",
    dot: "bg-table-abnormal",
    label: "이상 감지",
    labelEn: "Abnormal"
  },
  vacant: {
    bg: "bg-table-vacant/20 border-table-vacant/50 active:bg-table-vacant/40",
    dot: "bg-table-vacant",
    label: "비어있음",
    labelEn: "Vacant"
  },
};

const TouchTableFloorPlan = () => {
  const [selectedTable, setSelectedTable] = useState<TableData | null>(null);

  return (
    <div className="rounded-2xl border border-border bg-card p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-lg sm:text-xl">📍</span>
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-foreground">Floor Plan</h3>
            <span className="text-xs text-muted-foreground">테이블 현황</span>
          </div>
        </div>
        <Badge variant="outline" className="text-xs bg-success/20 text-success border-success/30">
          8/10 사용중
        </Badge>
      </div>

      {/* Legend - Horizontal scroll on mobile */}
      <div className="flex gap-3 mb-4 overflow-x-auto pb-2 scrollbar-thin">
        {Object.entries(statusConfig).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1.5 flex-shrink-0">
            <div className={cn("w-2.5 h-2.5 rounded-full", config.dot)} />
            <span className="text-[10px] sm:text-xs text-muted-foreground whitespace-nowrap">{config.label}</span>
          </div>
        ))}
      </div>

      {/* Table Grid - Touch optimized */}
      <div className="grid grid-cols-5 gap-2 sm:gap-3">
        {tables.map((table) => {
          const config = statusConfig[table.status];
          
          return (
            <Drawer key={table.id}>
              <DrawerTrigger asChild>
                <button
                  onClick={() => setSelectedTable(table)}
                  className={cn(
                    "aspect-square rounded-xl sm:rounded-2xl border-2 flex flex-col items-center justify-center",
                    "transition-all duration-200 touch-manipulation",
                    "min-h-[56px] sm:min-h-[72px]",
                    config.bg
                  )}
                >
                  <span className="text-base sm:text-lg font-bold text-foreground">{table.id}</span>
                  {table.customers !== undefined && (
                    <span className="text-[10px] sm:text-xs text-muted-foreground">👥{table.customers}</span>
                  )}
                </button>
              </DrawerTrigger>
              <DrawerContent className="bg-card border-border">
                <DrawerHeader className="pb-4">
                  <DrawerTitle className="flex items-center justify-between">
                    <span className="text-foreground">테이블 {table.id}</span>
                    <Badge variant="outline" className={cn(
                      "text-xs",
                      table.status === "occupied" && "bg-success/20 text-success border-success/30",
                      table.status === "cleaning" && "bg-warning/20 text-warning border-warning/30",
                      table.status === "abnormal" && "bg-destructive/20 text-destructive border-destructive/30",
                      table.status === "vacant" && "bg-muted text-muted-foreground border-border"
                    )}>
                      {config.label}
                    </Badge>
                  </DrawerTitle>
                </DrawerHeader>
                <div className="px-4 pb-8 space-y-4">
                  {/* Table Details */}
                  <div className="grid grid-cols-2 gap-3">
                    {table.customers !== undefined && (
                      <div className="p-4 rounded-xl bg-muted/30 border border-border">
                        <p className="text-xs text-muted-foreground mb-1">고객 수</p>
                        <p className="text-xl font-bold text-foreground">{table.customers}명</p>
                      </div>
                    )}
                    {table.occupancyTime && (
                      <div className="p-4 rounded-xl bg-muted/30 border border-border">
                        <p className="text-xs text-muted-foreground mb-1">체류 시간</p>
                        <p className="text-xl font-bold text-foreground">{table.occupancyTime}</p>
                      </div>
                    )}
                    {table.orderAmount && (
                      <div className="p-4 rounded-xl bg-accent/10 border border-accent/30 col-span-2">
                        <p className="text-xs text-muted-foreground mb-1">주문 금액</p>
                        <p className="text-2xl font-bold text-accent">{table.orderAmount}</p>
                      </div>
                    )}
                  </div>

                  {/* Quick Actions */}
                  <div className="flex gap-2">
                    {table.status === "occupied" && (
                      <>
                        <Button variant="outline" className="flex-1 h-12 text-sm">
                          🔍 CCTV 보기
                        </Button>
                        <Button variant="outline" className="flex-1 h-12 text-sm">
                          💳 결제 내역
                        </Button>
                      </>
                    )}
                    {table.status === "cleaning" && (
                      <Button className="flex-1 h-12 text-sm bg-success hover:bg-success/90">
                        ✅ 청소 완료
                      </Button>
                    )}
                    {table.status === "abnormal" && (
                      <>
                        <Button variant="destructive" className="flex-1 h-12 text-sm">
                          🚨 긴급 확인
                        </Button>
                        <Button variant="outline" className="flex-1 h-12 text-sm">
                          🔍 CCTV 보기
                        </Button>
                      </>
                    )}
                    {table.status === "vacant" && (
                      <Button variant="outline" className="flex-1 h-12 text-sm text-muted-foreground" disabled>
                        테이블 비어있음
                      </Button>
                    )}
                  </div>
                </div>
              </DrawerContent>
            </Drawer>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div className="mt-4 pt-4 border-t border-border grid grid-cols-3 gap-2 text-center">
        <div>
          <p className="text-lg sm:text-xl font-bold text-success">6</p>
          <p className="text-[10px] sm:text-xs text-muted-foreground">사용중</p>
        </div>
        <div>
          <p className="text-lg sm:text-xl font-bold text-warning">1</p>
          <p className="text-[10px] sm:text-xs text-muted-foreground">청소필요</p>
        </div>
        <div>
          <p className="text-lg sm:text-xl font-bold text-destructive">2</p>
          <p className="text-[10px] sm:text-xs text-muted-foreground">이상감지</p>
        </div>
      </div>
    </div>
  );
};

export default TouchTableFloorPlan;
