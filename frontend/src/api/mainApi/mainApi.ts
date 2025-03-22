import { instance } from "../api-instance.ts";

export const mainApi = {
  getTags() {
    return instance.get("landings/tags");
  },

  getLanding(pageName: any) {
    return instance.get(`landings/detail/by-page/${pageName}`);
  },

  buyCourse(data: any) {
    return instance.post(`stripe/checkout`, data);
  },
};
