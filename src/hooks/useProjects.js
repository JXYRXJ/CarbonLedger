import { useQuery } from "@tanstack/react-query";
import { projectApi } from "@/services/projectApi.js";

export const useProjects = (params) =>
  useQuery({ queryKey: ["projects", params], queryFn: () => projectApi.list(params) });

export const useProject = (id) =>
  useQuery({ queryKey: ["project", id], queryFn: () => projectApi.get(id), enabled: !!id });