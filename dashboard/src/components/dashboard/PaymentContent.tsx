import { useState, useEffect, useMemo } from "react";
import { CreditCard, Search, Filter, CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Transaction, TransactionStatus } from "@/api/types";
import { fetchTransactions } from "@/api/paymentApi";

const PaymentContent = () => {
  const [filter, setFilter] = useState<TransactionStatus | "ALL">("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const data = await fetchTransactions();
        setTransactions(data);
      } catch (err) {
        console.error("Payment data fetch error:", err);
        setError(err instanceof Error ? err.message : "데이터를 불러오는데 실패했습니다");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const filteredTransactions = useMemo(() => {
    return transactions.filter((t) => {
      const matchesFilter = filter === "ALL" || t.status === filter;
      const matchesSearch = t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           t.product.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [transactions, filter, searchQuery]);

  const stats = useMemo(() => ({
    auto: transactions.filter(t => t.status === "AUTO").length,
    review: transactions.filter(t => t.status === "REVIEW").length,
    error: transactions.filter(t => t.status === "ERROR").length,
  }), [transactions]);

  const getStatusIcon = (status: TransactionStatus) => {
    switch (status) {
      case "AUTO": return <CheckCircle className="w-4 h-4 text-success" />;
      case "REVIEW": return <AlertCircle className="w-4 h-4 text-warning" />;
      case "ERROR": return <XCircle className="w-4 h-4 text-destructive" />;
    }
  };

  const getStatusBadge = (status: TransactionStatus) => {
    const styles: Record<TransactionStatus, string> = {
      AUTO: "bg-success/20 text-success",
      REVIEW: "bg-warning/20 text-warning",
      ERROR: "bg-destructive/20 text-destructive",
    };
    return styles[status];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">결제 데이터를 불러오는 중...</p>
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
            <CreditCard className="w-7 h-7 text-primary" />
            결제 관리
          </h2>
          <p className="text-muted-foreground mt-1">Payment Management</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-success/20 text-success px-3 py-1.5 rounded-lg text-sm font-medium">
            AUTO: {stats.auto}
          </div>
          <div className="bg-warning/20 text-warning px-3 py-1.5 rounded-lg text-sm font-medium">
            REVIEW: {stats.review}
          </div>
          <div className="bg-destructive/20 text-destructive px-3 py-1.5 rounded-lg text-sm font-medium">
            ERROR: {stats.error}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-card rounded-2xl p-4 border border-border flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="거래 ID 또는 상품명 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          {(["ALL", "AUTO", "REVIEW", "ERROR"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                filter === status
                  ? "bg-primary text-primary-foreground"
                  : "bg-background border border-border text-muted-foreground hover:text-foreground"
              )}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-card rounded-2xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/50">
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">거래 ID</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">디바이스</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">고객</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">상품명</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">금액</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">시간</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">상태</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">액션</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-muted-foreground">
                    거래 내역이 없습니다
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((transaction, index) => (
                  <tr
                    key={transaction.id}
                    className={cn(
                      "border-t border-border transition-colors hover:bg-muted/30",
                      transaction.status === "REVIEW" && "bg-warning/5",
                      transaction.status === "ERROR" && "bg-destructive/5"
                    )}
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <td className="px-6 py-4 text-sm font-mono text-foreground">{transaction.id}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{transaction.device}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{transaction.customer || "-"}</td>
                    <td className="px-6 py-4 text-sm text-foreground">{transaction.product}</td>
                    <td className="px-6 py-4 text-sm font-semibold text-primary">{transaction.amount}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{transaction.time}</td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
                        getStatusBadge(transaction.status)
                      )}>
                        {getStatusIcon(transaction.status)}
                        {transaction.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {transaction.status === "REVIEW" && (
                        <button className="px-3 py-1.5 bg-primary/20 text-primary rounded-lg text-xs font-medium hover:bg-primary/30 transition-colors">
                          승인
                        </button>
                      )}
                      {transaction.status === "ERROR" && (
                        <button className="px-3 py-1.5 bg-destructive/20 text-destructive rounded-lg text-xs font-medium hover:bg-destructive/30 transition-colors">
                          재시도
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PaymentContent;
