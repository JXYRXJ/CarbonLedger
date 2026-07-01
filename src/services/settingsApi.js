import api from "./axios.js";

export const settingsApi = {
  getProfile: () => api.get("/settings/profile").then((r) => r.data),
  updateProfile: (payload) => api.put("/settings/profile", payload).then((r) => r.data),
  changePassword: (payload) => api.put("/settings/password", payload).then((r) => r.data),
  getNotifications: () => api.get("/settings/notifications").then((r) => r.data),
  updateNotifications: (payload) => api.put("/settings/notifications", payload).then((r) => r.data),
};