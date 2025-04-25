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

  getTokenAfterPurchase(data: any) {
    return instance.post(`stripe/complete-purchase`, data);
  },

  getCourseCards(params: any) {
    return instance.get(`landings/cards`, { params: params });
  },

  searchCourses(query: string, language: string, signal?: any) {
    return instance.get(`landings/search`, {
      params: {
        language: language,
        q: query,
      },
      signal,
    });
  },

  getProfessorDetail(id: number) {
    return instance.get(`/authors/full_detail/${id}`);
  },
};
