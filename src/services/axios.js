import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: { "Content-Type": "application/json" },
});

const unwrapApiPayload = (payload) => {
  if (payload && typeof payload === "object" && "data" in payload && "success" in payload) {
    return payload.data;
  }
  return payload;
};

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cl_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let queue = [];
const flush = (err, token) => {
  queue.forEach((p) => (err ? p.reject(err) : p.resolve(token)));
  queue = [];
};

api.interceptors.response.use(
  (response) => {
    if (response?.data) {
      return { ...response, data: unwrapApiPayload(response.data) };
    }
    return response;
  },
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          queue.push({
            resolve: (token) => {
              original.headers.Authorization = `Bearer ${token}`;
              resolve(api(original));
            },
            reject,
          });
        });
      }
      original._retry = true;
      isRefreshing = true;
      try {
        const refresh = localStorage.getItem("cl_refresh");
        if (!refresh) throw new Error("no refresh token");
        const { data: refreshPayload } = await axios.post(
          `${import.meta.env.VITE_API_URL || "/api"}/auth/refresh`,
          { refresh_token: refresh }
        );
        const refreshData = unwrapApiPayload(refreshPayload);
        const nextToken = refreshData?.access_token || refreshData?.token;
        const nextRefreshToken = refreshData?.refresh_token || refresh;
        localStorage.setItem("cl_token", nextToken);
        localStorage.setItem("cl_refresh", nextRefreshToken);
        flush(null, nextToken);
        original.headers.Authorization = `Bearer ${nextToken}`;
        return api(original);
      } catch (e) {
        flush(e, null);
        localStorage.removeItem("cl_token");
        localStorage.removeItem("cl_refresh");
        localStorage.removeItem("cl_user");
        if (typeof window !== "undefined") window.location.href = "/login";
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
