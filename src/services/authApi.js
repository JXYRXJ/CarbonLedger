import api from "./axios.js";

export const authApi = {
  login: (payload) => api.post("/auth/login", payload).then((r) => r.data),
  register: (payload) => api.post("/auth/register", payload).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),
  logout: (payload) => api.post("/auth/logout", payload).then((r) => r.data),
};
