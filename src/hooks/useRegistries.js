import { useQuery } from "@tanstack/react-query";
import { registryApi } from "@/services/registryApi.js";

export const useRegistries = (params) =>
  useQuery({ queryKey: ["registries", params], queryFn: () => registryApi.list(params) });

export const useRegistry = (id) =>
  useQuery({ queryKey: ["registry", id], queryFn: () => registryApi.get(id), enabled: !!id });