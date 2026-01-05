// ============================================
// 결제 API - central-api /orders 엔드포인트 연결
// ============================================

import type { Transaction, TransactionStatus, OrderHdrOut } from "./types";
import { apiFetch, formatToKST } from "./config";

/**
 * central-api Order -> dashboard Transaction 변환
 * dashboardApi에서도 재사용됨
 * @param order - 주문 데이터
 * @param separator - 여러 상품을 구분할 문자 (기본값: ", ")
 */
export function orderToTransaction(order: OrderHdrOut, separator: string = ", "): Transaction {
  // 메뉴 아이템 이름 사용 (없으면 item_id 표시)
  const productNames = order.lines
    .map(l => l.item_name || `Item #${l.item_id}`)
    .join(separator);

  // 주문 상태를 트랜잭션 상태로 매핑
  let status: TransactionStatus = "AUTO";
  if (order.status === "PENDING") status = "REVIEW";
  else if (order.status === "CANCELLED") status = "ERROR";

  return {
    id: `ORD-${order.order_id}`,
    device: order.store_name || `Store ${order.store_id}`,  // 매장명 사용 (없으면 store_id)
    product: productNames || "상품 없음",
    amount: `${order.total_amount_won.toLocaleString()}원`,
    status,
    time: formatToKST(order.created_at),
  };
}

export interface TransactionFilter {
  status?: TransactionStatus | "ALL";
  searchQuery?: string;
  storeId?: number;
}

export interface TransactionStats {
  auto: number;
  review: number;
  error: number;
  total: number;
}

/**
 * 주문 목록 조회 (필터 적용)
 */
export async function fetchTransactions(filter?: TransactionFilter): Promise<Transaction[]> {
  const params = new URLSearchParams();
  if (filter?.storeId) params.append("store_id", filter.storeId.toString());

  const queryString = params.toString() ? `?${params.toString()}` : "";
  const orders = await apiFetch<OrderHdrOut[]>(`/orders${queryString}`);

  // 결제관리 페이지에서는 쉼표로 구분
  let result = orders.map(order => orderToTransaction(order, ", "));

  // 클라이언트 측 필터링 (상태, 검색어)
  if (filter?.status && filter.status !== "ALL") {
    result = result.filter(t => t.status === filter.status);
  }

  if (filter?.searchQuery) {
    const query = filter.searchQuery.toLowerCase();
    result = result.filter(t =>
      t.id.toLowerCase().includes(query) ||
      t.product.toLowerCase().includes(query)
    );
  }

  return result;
}

/**
 * 트랜잭션 통계 조회 (주문 데이터 기반)
 */
export async function fetchTransactionStats(): Promise<TransactionStats> {
  const orders = await apiFetch<OrderHdrOut[]>("/orders");
  const transactions = orders.map(order => orderToTransaction(order, ", "));

  return {
    auto: transactions.filter(t => t.status === "AUTO").length,
    review: transactions.filter(t => t.status === "REVIEW").length,
    error: transactions.filter(t => t.status === "ERROR").length,
    total: transactions.length,
  };
}

/**
 * 리뷰 트랜잭션 승인 (central-api에서 미지원 - 임시 구현)
 */
export async function approveTransaction(transactionId: string): Promise<Transaction> {
  console.warn("approveTransaction: central-api에서 직접 지원하지 않음");
  return {
    id: transactionId,
    device: "Unknown",
    product: "Unknown",
    amount: "0원",
    status: "AUTO",
  };
}

/**
 * 에러 트랜잭션 재시도 (central-api에서 미지원 - 임시 구현)
 */
export async function retryTransaction(transactionId: string): Promise<Transaction> {
  console.warn("retryTransaction: central-api에서 직접 지원하지 않음");
  return {
    id: transactionId,
    device: "Unknown",
    product: "Unknown",
    amount: "0원",
    status: "REVIEW",
  };
}
