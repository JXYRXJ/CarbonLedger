import api from "./axios.js";

export const marketplaceApi = {
  list: (params) => api.get("/marketplace", { params }).then((r) => r.data),
  get: (id) => api.get(`/marketplace/${id}`).then((r) => r.data),
  buy: (payload) => api.post("/orders", payload).then((r) => r.data),
};