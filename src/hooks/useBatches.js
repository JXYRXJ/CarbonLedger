import { useQuery } from "@tanstack/react-query";
import { batchApi } from "@/services/batchApi.js";

export const useBatches = (params) =>
  useQuery({ queryKey: ["batches", params], queryFn: () => batchApi.list(params) });

export const useBatch = (id) =>
  useQuery({ queryKey: ["batch", id], queryFn: () => batchApi.get(id), enabled: !!id });

export const useBatchOwnership = (id) =>
  useQuery({ queryKey: ["batch-ownership", id], queryFn: () => batchApi.ownership(id), enabled: !!id });

export const useBatchTransactions = (id) =>
  useQuery({ queryKey: ["batch-transactions", id], queryFn: () => batchApi.transactions(id), enabled: !!id });

export const useBatchRetirements = (id) =>
  useQuery({ queryKey: ["batch-retirements", id], queryFn: () => batchApi.retirements(id), enabled: !!id });