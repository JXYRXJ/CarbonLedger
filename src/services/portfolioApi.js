import api from "./axios.js";

export const portfolioApi = {
  get: (params) => api.get("/portfolio", { params }).then((r) => r.data),
  summary: () => api.get("/portfolio/summary").then((r) => r.data),
};