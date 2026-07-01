import api from "./axios.js";

export const projectApi = {
  list: (params) => api.get("/projects", { params }).then((r) => r.data),
  get: (id) => api.get(`/projects/${id}`).then((r) => r.data),
};