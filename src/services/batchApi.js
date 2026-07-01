import api from "./axios.js";

export const batchApi = {
  list: (params) => api.get("/batches", { params }).then((r) => r.data),
  get: (id) => api.get(`/batches/${id}`).then((r) => r.data),
  ownership: (id) => api.get(`/batches/${id}/ownership`).then((r) => r.data),
  transactions: (id) => api.get(`/batches/${id}/transactions`).then((r) => r.data),
  retirements: (id) => api.get(`/batches/${id}/retirements`).then((r) => r.data),
};