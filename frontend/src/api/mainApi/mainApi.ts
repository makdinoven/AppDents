import { instance } from "../api-instance.ts";
import { getFacebookData } from "../../common/helpers/helpers.ts";
import { ParamsType } from "../adminApi/types.ts";

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

  searchCourses(params: { q: string; language: string }) {
    return instance.get(`landings/search`, {
      params,
    });
  },

  getProfessors(params: ParamsType) {
    return instance.get("authors/", {
      params: params,
    });
  },
  searchProfessors(params: ParamsType) {
    return instance.get("authors/search", {
      params: params,
    });
  },
  getProfessorDetail(id: number) {
    return instance.get(`/authors/full_detail/${id}`);
  },
};
