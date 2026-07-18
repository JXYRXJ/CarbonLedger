import api from "./axios.js";

export const settingsApi = {
  getProfile: () => api.get("/auth/me").then((r) => r.data),
  updateProfile: (payload) => api.patch("/users/profile", payload).then((r) => r.data),
  changePassword: (payload) => api.patch("/users/change-password", payload).then((r) => r.data),
  updateCompany: (payload) => api.patch("/companies", payload).then((r) => r.data),
  getNotifications: () => Promise.resolve({}),
  updateNotifications: (payload) => Promise.resolve(payload),
};