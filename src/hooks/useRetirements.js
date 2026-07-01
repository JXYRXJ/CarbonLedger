import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { retirementApi } from "@/services/retirementApi.js";

export const useRetirements = (params) =>
  useQuery({ queryKey: ["retirements", params], queryFn: () => retirementApi.list(params) });

export const useRetirementStats = () =>
  useQuery({ queryKey: ["retirements-stats"], queryFn: () => retirementApi.stats() });

export const useRetire = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: retirementApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["retirements"] });
      qc.invalidateQueries({ queryKey: ["retirements-stats"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
};