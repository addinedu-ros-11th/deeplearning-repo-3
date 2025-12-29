import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { Transaction, TransactionStatus } from "@/api/types";

const statusConfig: Record<TransactionStatus, {
  label: string;
  badge: string;
  row: string;
}> = {
  AUTO: {
    label: "✅ AUTO",
    badge: "bg-success/20 text-success border-success/30",
    row: "hover:bg-muted/30"
  },
  REVIEW: {
    label: "🟡 REVIEW",
    badge: "bg-warning/20 text-warning border-warning/30",
    row: "bg-warning/10 hover:bg-warning/20"
  },
  ERROR: {
    label: "❌ ERROR",
    badge: "bg-destructive/20 text-destructive border-destructive/30",
    row: "bg-destructive/10 hover:bg-destructive/20"
  },
};

interface TransactionLogProps {
  transactions?: Transaction[];
}

const TransactionLog = ({ transactions = [] }: TransactionLogProps) => {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">💳</span>
        <h3 className="text-lg font-semibold text-foreground">Recent Transactions</h3>
        <span className="text-sm text-muted-foreground ml-2">최근 거래 내역</span>
      </div>

      {/* Status Legend */}
      <div className="flex gap-3 mb-4">
        {Object.entries(statusConfig).map(([key, config]) => (
          <div key={key} className="flex items-center gap-1">
            <Badge variant="outline" className={cn("text-xs px-2 py-0.5", config.badge)}>
              {config.label}
            </Badge>
          </div>
        ))}
      </div>

      {transactions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          거래 내역이 없습니다
        </div>
      ) : (
        <>
          {/* Transaction List */}
          <div className="flex-1 overflow-auto scrollbar-thin">
            <table className="w-full">
              <thead className="sticky top-0 bg-card">
                <tr className="text-xs text-muted-foreground border-b border-border">
                  <th className="text-left py-3 px-2 font-medium w-[15%]">ID</th>
                  <th className="text-left py-3 px-2 font-medium w-[15%]">기기</th>
                  <th className="text-left py-3 px-2 font-medium w-[35%]">상품</th>
                  <th className="text-right py-3 px-2 font-medium w-[15%]">금액</th>
                  <th className="text-right py-3 px-2 font-medium w-[20%]">상태</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx, index) => {
                  const config = statusConfig[tx.status];
                  return (
                    <tr
                      key={tx.id}
                      className={cn(
                        "border-b border-border/50 transition-colors cursor-pointer",
                        config.row
                      )}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <td className="py-3 px-2 w-[15%]">
                        <span className="text-sm font-mono text-muted-foreground">{tx.id}</span>
                      </td>
                      <td className="py-3 px-2 w-[15%]">
                        <span className="text-sm text-foreground">{tx.device}</span>
                      </td>
                      <td className="py-3 px-2 w-[35%]">
                        <span className="text-sm text-foreground whitespace-pre-line">{tx.product}</span>
                      </td>
                      <td className="py-3 px-2 text-right w-[15%]">
                        <span className="text-sm font-medium text-accent">{tx.amount}</span>
                      </td>
                      <td className="py-3 px-2 text-right w-[20%]">
                        <Badge variant="outline" className={cn("text-xs", config.badge)}>
                          {tx.status}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="mt-4 pt-4 border-t border-border flex justify-between text-sm">
            <span className="text-muted-foreground">총 거래</span>
            <span className="text-foreground font-medium">{transactions.length}건</span>
          </div>
        </>
      )}
    </div>
  );
};

export default TransactionLog;
