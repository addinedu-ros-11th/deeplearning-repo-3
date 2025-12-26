import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { TableData, TableStatus } from "@/api/types";

const statusConfig: Record<TableStatus, {
  bg: string;
  dot: string;
  label: string;
  labelEn: string;
}> = {
  occupied: {
    bg: "bg-table-occupied/20 border-table-occupied/50 hover:bg-table-occupied/30",
    dot: "bg-table-occupied",
    label: "사용중",
    labelEn: "Occupied"
  },
  cleaning: {
    bg: "bg-table-cleaning/20 border-table-cleaning/50 hover:bg-table-cleaning/30",
    dot: "bg-table-cleaning",
    label: "청소 필요",
    labelEn: "Needs Cleaning"
  },
  abnormal: {
    bg: "bg-table-abnormal/20 border-table-abnormal/50 hover:bg-table-abnormal/30 animate-pulse-soft",
    dot: "bg-table-abnormal",
    label: "이상 감지",
    labelEn: "Abnormal"
  },
  vacant: {
    bg: "bg-table-vacant/20 border-table-vacant/50 hover:bg-table-vacant/30",
    dot: "bg-table-vacant",
    label: "비어있음",
    labelEn: "Vacant"
  },
};

interface TableFloorPlanProps {
  tables?: TableData[];
}

const TableFloorPlan = ({ tables = [] }: TableFloorPlanProps) => {
  const occupiedCount = tables.filter(t => t.status === "occupied").length;
  const totalCount = tables.length;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 h-full">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-xl">📍</span>
        <h3 className="text-lg font-semibold text-foreground">Table Floor Plan</h3>
        <span className="text-sm text-muted-foreground ml-2">테이블 현황</span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-6">
        {Object.entries(statusConfig).map(([key, config]) => (
          <div key={key} className="flex items-center gap-2">
            <div className={cn("w-3 h-3 rounded-full", config.dot)} />
            <span className="text-xs text-muted-foreground">{config.label}</span>
          </div>
        ))}
      </div>

      {tables.length === 0 ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          테이블 데이터가 없습니다
        </div>
      ) : (
        <>
          {/* Table Grid */}
          <div className="grid grid-cols-5 gap-3">
            {tables.map((table) => {
              const config = statusConfig[table.status];

              return (
                <Tooltip key={table.id}>
                  <TooltipTrigger asChild>
                    <div
                      className={cn(
                        "aspect-square rounded-xl border-2 flex flex-col items-center justify-center cursor-pointer transition-all duration-200",
                        config.bg
                      )}
                    >
                      <span className="text-lg font-bold text-foreground">{table.id}</span>
                      {table.customers !== undefined && (
                        <span className="text-xs text-muted-foreground mt-1">👥 {table.customers}</span>
                      )}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="bg-card border-border p-3">
                    <div className="space-y-1">
                      <p className="font-semibold">Table {table.id}</p>
                      <p className="text-sm text-muted-foreground">
                        상태: <span className={cn(
                          table.status === "occupied" && "text-success",
                          table.status === "cleaning" && "text-warning",
                          table.status === "abnormal" && "text-destructive",
                          table.status === "vacant" && "text-muted-foreground"
                        )}>{config.label}</span>
                      </p>
                      {table.customers !== undefined && (
                        <p className="text-sm text-muted-foreground">고객 수: {table.customers}명</p>
                      )}
                      {table.occupancyTime && (
                        <p className="text-sm text-muted-foreground">체류 시간: {table.occupancyTime}</p>
                      )}
                      {table.orderAmount && (
                        <p className="text-sm text-accent font-medium">주문 금액: {table.orderAmount}</p>
                      )}
                    </div>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>

          {/* Summary */}
          <div className="mt-6 pt-4 border-t border-border">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">총 테이블</span>
              <span className="text-foreground font-medium">{totalCount}</span>
            </div>
            <div className="flex justify-between text-sm mt-1">
              <span className="text-muted-foreground">사용중</span>
              <span className="text-success font-medium">
                {occupiedCount} ({totalCount > 0 ? Math.round((occupiedCount / totalCount) * 100) : 0}%)
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TableFloorPlan;
