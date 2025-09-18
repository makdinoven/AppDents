import axios from "axios";
import { BASE_URL } from "../common/helpers/commonConstants.ts";

export const instance = axios.create({
  baseURL: BASE_URL,
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
