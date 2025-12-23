import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ChevronRight } from "lucide-react";

interface Transaction {
  id: string;
  device: string;
  product: string;
  amount: string;
  status: "AUTO" | "REVIEW" | "ERROR";
  time: string;
}

const transactions: Transaction[] = [
  { id: "TXN001", device: "01", product: "크루아상", amount: "₩5,000", status: "AUTO", time: "14:32" },
  { id: "TXN002", device: "02", product: "식빵+크림", amount: "₩15,000", status: "REVIEW", time: "14:28" },
  { id: "TXN003", device: "01", product: "베이글", amount: "₩4,000", status: "AUTO", time: "14:25" },
  { id: "TXN004", device: "03", product: "초코칩 쿠키", amount: "₩6,500", status: "AUTO", time: "14:20" },
  { id: "TXN005", device: "02", product: "도넛 세트", amount: "₩12,000", status: "AUTO", time: "14:15" },
];

const statusConfig = {
  AUTO: {
    label: "✅",
    badge: "bg-success/20 text-success border-success/30",
  },
  REVIEW: {
    label: "🟡",
    badge: "bg-warning/20 text-warning border-warning/30",
  },
  ERROR: {
    label: "❌",
    badge: "bg-destructive/20 text-destructive border-destructive/30",
  },
};

const MobileTransactionList = () => {
  return (
    <div className="rounded-2xl border border-border bg-card overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-lg">💳</span>
          <div>
            <h3 className="text-base font-semibold text-foreground">최근 거래</h3>
            <span className="text-xs text-muted-foreground">Recent Transactions</span>
          </div>
        </div>
        <button className="text-xs text-primary font-medium flex items-center gap-1">
          전체보기 <ChevronRight className="w-3 h-3" />
        </button>
      </div>

      <div className="divide-y divide-border">
        {transactions.map((tx) => {
          const config = statusConfig[tx.status];
          return (
            <button
              key={tx.id}
              className={cn(
                "w-full p-4 flex items-center gap-3 text-left",
                "active:bg-muted/50 transition-colors touch-manipulation",
                tx.status === "REVIEW" && "bg-warning/5",
                tx.status === "ERROR" && "bg-destructive/5"
              )}
            >
              <div className="w-10 h-10 rounded-xl bg-muted/50 flex items-center justify-center text-lg flex-shrink-0">
                {config.label}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground truncate">{tx.product}</span>
                  <Badge variant="outline" className={cn("text-[10px] px-1.5 py-0", config.badge)}>
                    {tx.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-muted-foreground">기기 #{tx.device}</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">{tx.time}</span>
                </div>
              </div>
              <span className="text-sm font-semibold text-accent flex-shrink-0">{tx.amount}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default MobileTransactionList;
