import { instance } from "../api-instance.ts";
import {
  getAuthHeaders,
  getFacebookData,
} from "../../common/helpers/helpers.ts";
import { ParamsType } from "../adminApi/types.ts";
import { REF_CODE_LS_KEY } from "../../common/helpers/commonConstants.ts";

export const mainApi = {
  getTags() {
    return instance.get("landings/tags");
  },

  getLanding(pageName: any) {
    return instance.get(`landings/detail/by-page/${pageName}`);
  },

  trackLandingVisit(id: number) {
    return instance.post(`landings/${id}/visit`);
  },

  buyCourse(data: any, isLogged: boolean) {
    const { fbp, fbc } = getFacebookData();
    const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
    return instance.post(
      `stripe/checkout`,
      {
        ...data,
        fbp,
        fbc,
        ...(rcCode && { ref_code: rcCode }),
      },
      { headers: isLogged ? getAuthHeaders() : undefined },
    );
  },

  getFreeCourse(data: any, isLogged: boolean) {
    const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
    return instance.post(
      `landings/free-access/${data.id}`,
      {
        ...data,
        ...(rcCode && { ref_code: rcCode }),
      },
      { headers: isLogged ? getAuthHeaders() : undefined },
    );
  },

  getTokenAfterPurchase(data: any) {
    return instance.post(`stripe/complete-purchase`, data);
  },

  getCourseCards(params: any) {
    return instance.get(`landings/cards`, { params: params });
  },

  getCourseCardsRecommend(params: any) {
    return instance.get(`landings/recommend/cards`, {
      headers: getAuthHeaders(),
      params: params,
    });
  },

  getLandingCards(params: any) {
    return instance.get(`landings/v1/cards`, { params: params });
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

  trackFacebookAd(slug: string) {
    return instance.post(`/landings/track-ad/${slug}`);
  },
  globalSearch(params: {
    q: string;
    languages?: string[];
    limit?: number;
    types?: ("authors" | "landings" | "book_landings")[];
  }) {
    return instance.get(`/search/v2`, {
      params,
      paramsSerializer: (params) => {
        const searchParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          if (Array.isArray(value)) {
            value.forEach((v) => searchParams.append(key, v));
          } else if (value !== undefined && value !== null) {
            searchParams.append(key, String(value));
          }
        });
        return searchParams.toString();
      },
    });
  },
};
