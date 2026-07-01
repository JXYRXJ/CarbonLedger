import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/services/analyticsApi.js";

export const useAnalyticsOverview = (params) =>
  useQuery({ queryKey: ["analytics-overview", params], queryFn: () => analyticsApi.overview(params) });

export const usePortfolioGrowth = (params) =>
  useQuery({ queryKey: ["analytics-portfolio-growth", params], queryFn: () => analyticsApi.portfolioGrowth(params) });

export const useCreditsTraded = (params) =>
  useQuery({ queryKey: ["analytics-credits-traded", params], queryFn: () => analyticsApi.creditsTraded(params) });

export const useCreditsRetired = (params) =>
  useQuery({ queryKey: ["analytics-credits-retired", params], queryFn: () => analyticsApi.creditsRetired(params) });

export const useMarketplaceVolume = (params) =>
  useQuery({ queryKey: ["analytics-marketplace-volume", params], queryFn: () => analyticsApi.marketplaceVolume(params) });

export const useCountryDistribution = () =>
  useQuery({ queryKey: ["analytics-country-distribution"], queryFn: () => analyticsApi.countryDistribution() });

export const useProjectTypes = () =>
  useQuery({ queryKey: ["analytics-project-types"], queryFn: () => analyticsApi.projectTypes() });