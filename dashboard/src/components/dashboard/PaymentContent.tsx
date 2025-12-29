import { useState, useEffect, useMemo } from "react";
import { CreditCard, Search } from "lucide-react";
import type { Transaction } from "@/api/types";
import { fetchTransactions } from "@/api/paymentApi";

const PaymentContent = () => {
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
      const matchesSearch = t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           t.product.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [transactions, searchQuery]);

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
      <div>
        <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <CreditCard className="w-7 h-7 text-primary" />
          결제 관리
        </h2>
        <p className="text-muted-foreground mt-1">Payment Management</p>
      </div>

      {/* Search */}
      <div className="bg-card rounded-2xl p-4 border border-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="거래 ID 또는 상품명 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-card rounded-2xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/50">
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">거래 ID</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">매장명</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">상품명</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">금액</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-foreground">시간</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                    거래 내역이 없습니다
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((transaction, index) => (
                  <tr
                    key={transaction.id}
                    className="border-t border-border transition-colors hover:bg-muted/30"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <td className="px-6 py-4 text-sm font-mono text-foreground">{transaction.id}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{transaction.device}</td>
                    <td className="px-6 py-4 text-sm text-foreground">{transaction.product}</td>
                    <td className="px-6 py-4 text-sm font-semibold text-primary">{transaction.amount}</td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">{transaction.time}</td>
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
