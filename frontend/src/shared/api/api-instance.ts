import axios from "axios";
import { BASE_URL } from "../common/helpers/commonConstants.ts";
import { Alert } from "../components/ui/Alert/Alert.tsx";
import { t } from "i18next";

export const instance = axios.create({
  baseURL: `${BASE_URL}/api`,
  withCredentials: false,
  paramsSerializer: (params) => {
    const searchParams = new URLSearchParams();
    for (const key in params) {
      const value = params[key];
      if (Array.isArray(value)) {
        value.forEach((v) => searchParams.append(key, v));
      } else if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    }
    return searchParams.toString();
  },
});

instance.interceptors.request.use((config) => {
  return config;
});

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status === 429) {
      Alert(`${t("tooManyRequests")}`);
    }
    return Promise.reject(error);
  },
);
