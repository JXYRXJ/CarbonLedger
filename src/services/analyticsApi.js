import api from "./axios.js";

export const analyticsApi = {
  overview: (params) => api.get("/analytics/overview", { params }).then((r) => r.data),
  portfolioGrowth: (params) => api.get("/analytics/portfolio-growth", { params }).then((r) => r.data),
  creditsTraded: (params) => api.get("/analytics/credits-traded", { params }).then((r) => r.data),
  creditsRetired: (params) => api.get("/analytics/credits-retired", { params }).then((r) => r.data),
  marketplaceVolume: (params) => api.get("/analytics/marketplace-volume", { params }).then((r) => r.data),
  countryDistribution: () => api.get("/analytics/country-distribution").then((r) => r.data),
  projectTypes: () => api.get("/analytics/project-types").then((r) => r.data),
};