import api from "./axios.js";

export const walletApi = {
  get: () => api.get("/companies/me").then((r) => r.data),
  connect: (payload) => api.patch("/companies/wallet", { wallet_address: payload.wallet_address || payload.address || payload.walletAddress || "" }).then((r) => r.data),
  disconnect: () => Promise.resolve({}),
  transactions: (params) => api.get("/wallet/transactions", { params }).then((r) => r.data),
};