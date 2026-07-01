import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/services/adminApi.js";

export const useAdminOverview = () =>
  useQuery({ queryKey: ["admin-overview"], queryFn: () => adminApi.overview() });

export const useAdminUsers = (params) =>
  useQuery({ queryKey: ["admin-users", params], queryFn: () => adminApi.users(params) });

export const useAdminRegistries = (params) =>
  useQuery({ queryKey: ["admin-registries", params], queryFn: () => adminApi.registries(params) });

export const useAdminProjects = (params) =>
  useQuery({ queryKey: ["admin-projects", params], queryFn: () => adminApi.projects(params) });

export const useAdminListings = (params) =>
  useQuery({ queryKey: ["admin-listings", params], queryFn: () => adminApi.listings(params) });

export const useAdminTransactions = (params) =>
  useQuery({ queryKey: ["admin-transactions", params], queryFn: () => adminApi.transactions(params) });

export const useAdminApprovals = (params) =>
  useQuery({ queryKey: ["admin-approvals", params], queryFn: () => adminApi.approvals(params) });