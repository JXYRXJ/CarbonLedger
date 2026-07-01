import api from "./axios.js";

export const registryApi = {
  list: (params) => api.get("/registries", { params }).then((r) => r.data),
  get: (id) => api.get(`/registries/${id}`).then((r) => r.data),
};