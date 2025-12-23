// ============================================
// Payment API - Functions to manage transactions
// Replace mock implementations with real FastAPI calls
// ============================================

import type { Transaction, TransactionStatus } from "./types";
import { mockTransactionsFull } from "./mockData";

// API Base URL - Change this when connecting to FastAPI
const API_BASE_URL = "/api";

// Simulated network delay for development
const simulateDelay = (ms: number = 100) => 
  new Promise(resolve => setTimeout(resolve, ms));

export interface TransactionFilter {
  status?: TransactionStatus | "ALL";
  searchQuery?: string;
}

export interface TransactionStats {
  auto: number;
  review: number;
  error: number;
  total: number;
}

/**
 * Fetch all transactions with optional filters
 */
export async function fetchTransactions(filter?: TransactionFilter): Promise<Transaction[]> {
  // TODO: Replace with real API call
  // const params = new URLSearchParams();
  // if (filter?.status && filter.status !== "ALL") params.append("status", filter.status);
  // if (filter?.searchQuery) params.append("q", filter.searchQuery);
  // const response = await fetch(`${API_BASE_URL}/transactions?${params}`);
  // return response.json();
  
  await simulateDelay();
  
  let result = [...mockTransactionsFull];
  
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
 * Get transaction statistics
 */
export async function fetchTransactionStats(): Promise<TransactionStats> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/transactions/stats`);
  // return response.json();
  
  await simulateDelay();
  
  const transactions = mockTransactionsFull;
  return {
    auto: transactions.filter(t => t.status === "AUTO").length,
    review: transactions.filter(t => t.status === "REVIEW").length,
    error: transactions.filter(t => t.status === "ERROR").length,
    total: transactions.length,
  };
}

/**
 * Approve a REVIEW transaction
 */
export async function approveTransaction(transactionId: string): Promise<Transaction> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}/approve`, {
  //   method: "POST",
  // });
  // return response.json();
  
  await simulateDelay();
  
  const transaction = mockTransactionsFull.find(t => t.id === transactionId);
  if (!transaction) throw new Error("Transaction not found");
  
  return { ...transaction, status: "AUTO" };
}

/**
 * Retry a failed ERROR transaction
 */
export async function retryTransaction(transactionId: string): Promise<Transaction> {
  // TODO: Replace with real API call
  // const response = await fetch(`${API_BASE_URL}/transactions/${transactionId}/retry`, {
  //   method: "POST",
  // });
  // return response.json();
  
  await simulateDelay();
  
  const transaction = mockTransactionsFull.find(t => t.id === transactionId);
  if (!transaction) throw new Error("Transaction not found");
  
  return { ...transaction, status: "REVIEW" };
}
