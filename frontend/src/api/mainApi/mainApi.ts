import { instance } from "../api-instance.ts";

export const mainApi = {
  getTags() {
    try {
      return instance.get("landings/tags");
    } catch (error) {
      return Promise.reject(error);
    }
  },
};
