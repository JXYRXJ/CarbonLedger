import { useQuery } from "@tanstack/react-query";
import { portfolioApi } from "@/services/portfolioApi.js";

export const usePortfolio = (params) =>
  useQuery({ queryKey: ["portfolio", params], queryFn: () => portfolioApi.get(params) });

export const usePortfolioSummary = () =>
  useQuery({ queryKey: ["portfolio-summary"], queryFn: () => portfolioApi.summary() });