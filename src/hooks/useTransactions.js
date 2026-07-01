import { useQuery } from "@tanstack/react-query";
import { transactionApi } from "@/services/transactionApi.js";

export const useTransactions = (params) =>
  useQuery({ queryKey: ["transactions", params], queryFn: () => transactionApi.list(params) });