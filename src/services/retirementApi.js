import api from "./axios.js";

export const retirementApi = {
  list: (params) => api.get("/retirements", { params }).then((r) => r.data),
  stats: () => api.get("/retirements/stats").then((r) => r.data),
  create: (payload) => api.post("/retirements", payload).then((r) => r.data),
};