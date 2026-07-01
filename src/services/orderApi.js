import api from "./axios.js";

export const orderApi = {
  list: (params) => api.get("/orders", { params }).then((r) => r.data),
  get: (id) => api.get(`/orders/${id}`).then((r) => r.data),
};