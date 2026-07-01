import api from "./axios.js";

export const walletApi = {
  get: () => api.get("/wallet").then((r) => r.data),
  connect: (payload) => api.post("/wallet/connect", payload).then((r) => r.data),
  disconnect: () => api.post("/wallet/disconnect").then((r) => r.data),
  transactions: (params) => api.get("/wallet/transactions", { params }).then((r) => r.data),
};