import { useQuery } from "@tanstack/react-query";
import { orderApi } from "@/services/orderApi.js";

export const useOrders = (params) =>
  useQuery({ queryKey: ["orders", params], queryFn: () => orderApi.list(params) });