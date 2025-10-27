import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";
import { ParamsType } from "../adminApi/types.ts";
import { REF_CODE_LS_KEY } from "../../common/helpers/commonConstants.ts";
import { PaymentApiPayload } from "../../store/slices/paymentSlice.ts";

export const mainApi = {
  getTags() {
    return instance.get("landings/tags");
  },

  getLanding(pageName: any) {
    return instance.get(`landings/detail/by-page/${pageName}`);
  },

  getBookLanding(pageName: any) {
    return instance.get(`books/landing/slug/${pageName}`);
  },
  getBook(id: any) {
    return instance.get(`books/me/books/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  trackLandingVisit(id: number, ad: boolean) {
    return instance.post(`landings/${id}/visit`, { from_ad: ad });
  },

  buyCourse(data: PaymentApiPayload, isLogged: boolean) {
    return instance.post(`stripe/checkout`, data, {
      headers: isLogged ? getAuthHeaders() : undefined,
    });
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

  getBookCards(params: any) {
    return instance.get(`landings/cards`, { params: params });
  },

  getCourseCardsRecommend(params: any) {
    return instance.get(`landings/recommend/cards`, {
      headers: getAuthHeaders(),
      params: params,
    });
  },

  getBookCardsRecommend(params: any) {
    return instance.get(`landings/recommend/cards`, {
      headers: getAuthHeaders(),
      params: params,
    });
  },

  getLandingCards(params: any) {
    return instance.get(`landings/v1/cards`, { params: params });
  },

  getBookLandingCards(params: any) {
    return instance.get(`books/landing/cards`, { params: params });
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

  trackFacebookAd(slug: string, fbc: any, fbp: any) {
    return instance.post(`/landings/track-ad/${slug}`, { fbc, fbp });
  },
  globalSearch(params: {
    q: string;
    languages?: string[];
    limit?: number;
    types?: ("authors" | "landings" | "book_landings")[];
  }) {
    return instance.get(`/search/v2`, {
      params,
    });
  },
  getPageInfo(pageType: string, language: string) {
    return instance.get(`/policy/${pageType}?language=${language}`);
  },
};
