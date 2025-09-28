import axios from "axios";

export const instance = axios.create({
  baseURL: "https://dent-s.com/api",
  withCredentials: false,
});

instance.interceptors.request.use((config) => {
  return config;
});

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  },
);
