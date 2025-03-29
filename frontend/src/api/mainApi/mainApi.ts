import { instance } from "../api-instance.ts";
import { getFacebookData } from "../../common/helpers/helpers.ts";

export const mainApi = {
  getTags() {
    return instance.get("landings/tags");
  },

  getLanding(pageName: any) {
    return instance.get(`landings/detail/by-page/${pageName}`);
  },

  buyCourse(data: any) {
    const { fbp, fbc } = getFacebookData();
    return instance.post(`stripe/checkout`, {
      ...data,
      fbp,
      fbc,
    });
  },
};
