import api from "./axios.js";

export const transactionApi = {
  list: (params) => api.get("/transactions", { params }).then((r) => r.data),
  get: (id) => api.get(`/transactions/${id}`).then((r) => r.data),
};