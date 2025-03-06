import { instance } from "../api-instance.ts";

export const mainApi = {
  getTags() {
    try {
      return instance.get("landings/tags");
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getLanding(pageName: any) {
    try {
      return instance.get(`landings/detail/by-page/${pageName}`);
    } catch (error) {
      return Promise.reject(error);
    }
  },
};
