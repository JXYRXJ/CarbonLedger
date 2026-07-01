import api from "./axios.js";

export const listingApi = {
  list: (params) => api.get("/listings", { params }).then((r) => r.data),
  create: (payload) => api.post("/listings", payload).then((r) => r.data),
  cancel: (id) => api.delete(`/listings/${id}`).then((r) => r.data),
};