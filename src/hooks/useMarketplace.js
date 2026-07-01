import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { marketplaceApi } from "@/services/marketplaceApi.js";

export const useMarketplace = (params) =>
  useQuery({ queryKey: ["marketplace", params], queryFn: () => marketplaceApi.list(params) });

export const useMarketplaceListing = (id) =>
  useQuery({ queryKey: ["marketplace", id], queryFn: () => marketplaceApi.get(id), enabled: !!id });

export const useBuy = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: marketplaceApi.buy,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["marketplace"] });
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};