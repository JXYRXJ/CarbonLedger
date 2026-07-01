import api from "./axios.js";

export const adminApi = {
  overview: () => api.get("/admin/overview").then((r) => r.data),
  users: (params) => api.get("/admin/users", { params }).then((r) => r.data),
  registries: (params) => api.get("/admin/registries", { params }).then((r) => r.data),
  projects: (params) => api.get("/admin/projects", { params }).then((r) => r.data),
  listings: (params) => api.get("/admin/listings", { params }).then((r) => r.data),
  transactions: (params) => api.get("/admin/transactions", { params }).then((r) => r.data),
  approvals: (params) => api.get("/admin/approvals", { params }).then((r) => r.data),
  approve: (id) => api.post(`/admin/approvals/${id}/approve`).then((r) => r.data),
  reject: (id) => api.post(`/admin/approvals/${id}/reject`).then((r) => r.data),
};