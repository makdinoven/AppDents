import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";
import { ParamsType } from "./types.ts";
import { SummaryToolDataType } from "../../pages/Admin/pages/tools/VideoSummaryTool/VideoSummaryTool.tsx";

export const adminApi = {
  getCoursesList(params: ParamsType) {
    return instance.get("courses/list", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  searchCourses(params: ParamsType) {
    return instance.get("courses/list/search", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  getCourse(id: any) {
    return instance.get(`courses/detail/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  createCourse(data: any) {
    return instance.post(`courses/`, data, {
      headers: getAuthHeaders(),
    });
  },
  deleteCourse(id: any) {
    return instance.delete(`courses/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  updateCourse(id: any, data: any) {
    return instance.put(`courses/${id}`, data, {
      headers: getAuthHeaders(),
    });
  },

  getLandingsList(params: ParamsType) {
    return instance.get("landings/list", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  searchLandings(params: ParamsType) {
    return instance.get("landings/list/search", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  getLanding(id: any) {
    return instance.get(`landings/detail/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  createLanding(data: any) {
    return instance.post(`landings/`, data, {
      headers: getAuthHeaders(),
    });
  },
  deleteLanding(id: any) {
    return instance.delete(`landings/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  updateLanding(id: any, data: any) {
    return instance.put(`landings/${id}`, data, {
      headers: getAuthHeaders(),
    });
  },
  toggleLandingVisibility(id: number, is_hidden: boolean) {
    return instance.patch(
      `landings/set-hidden/${id}?is_hidden=${is_hidden}`,
      {},
      {
        headers: getAuthHeaders(),
      },
    );
  },

  getBookLandingsList(params: ParamsType) {
    return instance.get("books/landing/list", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  searchBookLandings(params: ParamsType) {
    return instance.get("books/landing/list/search", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  getBookLanding(id: any) {
    return instance.get(`books/${id}/detail`, {
      headers: getAuthHeaders(),
    });
  },
  createBookLanding(data: any) {
    return instance.post(`books/landing`, data, {
      headers: getAuthHeaders(),
    });
  },
  deleteBookLanding(id: any) {
    return instance.delete(`books/landing/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  updateBookLanding(id: any, data: any) {
    return instance.put(`books/landings/${id}`, data, {
      headers: getAuthHeaders(),
    });
  },
  toggleBookLandingVisibility(id: number, is_hidden: boolean) {
    return instance.patch(
      `books/landings/set-hidden/${id}?is_hidden=${is_hidden}`,
      {},
      {
        headers: getAuthHeaders(),
      },
    );
  },

  getAuthorsList(params: ParamsType) {
    return instance.get("authors/", { params: params });
  },
  searchAuthors(params: ParamsType) {
    return instance.get("authors/search", { params: params });
  },
  getAuthor(id: any) {
    return instance.get(`authors/detail/${id}`);
  },
  createAuthor(data: any) {
    return instance.post("authors/", data, {
      headers: getAuthHeaders(),
    });
  },
  updateAuthor(id: any, data: any) {
    return instance.put(`authors/${id}`, data, {
      headers: getAuthHeaders(),
    });
  },
  deleteAuthor(id: any) {
    return instance.delete(`authors/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  getUsersList(params: ParamsType) {
    return instance.get("users/admin/users", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  searchUsers(params: ParamsType) {
    return instance.get("users/admin/users/search", {
      headers: getAuthHeaders(),
      params: params,
    });
  },
  getUser(id: any) {
    return instance.get(`users/admin/${id}/detail`, {
      headers: getAuthHeaders(),
    });
  },
  updateUser(id: any, data: any) {
    return instance.put(`users/${id}`, data, { headers: getAuthHeaders() });
  },
  createUser(data: any) {
    return instance.post("users/admin/users", data, {
      headers: getAuthHeaders(),
    });
  },
  deleteUser(id: any) {
    return instance.delete(`users/admin/${id}`, { headers: getAuthHeaders() });
  },
  changeUserBalance(data: {
    user_id: number;
    amount: number;
    meta: { reason: string };
  }) {
    return instance.post(`wallet/admin/adjust`, data, {
      headers: getAuthHeaders(),
    });
  },

  uploadPhoto(file: any) {
    return instance.post("photo/photo", file, { headers: getAuthHeaders() });
  },

  getMostPopularLandings(params: any) {
    return instance.get("landings/most-popular", {
      params: params,
      headers: getAuthHeaders(),
    });
  },
  getLanguageStats(params: any) {
    return instance.get("landings/analytics/language-stats", {
      params: params,
      headers: getAuthHeaders(),
    });
  },
  getReferrals(params: any) {
    return instance.get("users/analytics/referral-stats", {
      params: params,
      headers: getAuthHeaders(),
    });
  },
  getPurchases(params: any) {
    return instance.get("users/analytics/purchases", {
      params: params,
      headers: getAuthHeaders(),
    });
  },
  getUserGrowth(params: any) {
    return instance.get("users/analytics/user-growth", {
      params: params,
      headers: getAuthHeaders(),
    });
  },
  getFreewebStats(params: any) {
    return instance.get("users/analytics/free-course-stats", {
      params: params,
      headers: getAuthHeaders(),
    });
  },
  getClip(url: string) {
    return instance.post(
      "/clip_generator/clip",
      {
        url: url,
      },
      { headers: getAuthHeaders() },
    );
  },
  getClipStatus(id: string) {
    return instance.get(`/clip_generator/clip/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  getVideoSummary({ video_url, context, answer_format }: SummaryToolDataType) {
    return instance.post(
      "/summary_generator/video-summary",
      {
        video_url,
        ...(context && { context }),
        ...(answer_format && { answer_format }),
        final_model: "anthropic/claude-3-5-sonnet",
      },
      { headers: getAuthHeaders() },
    );
  },
  getVideoSummaryStatus(id: string) {
    return instance.get(`/summary_generator/video-summary/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  getPurchasesSourceChart(params: any) {
    return instance.get("users/analytics/purchase/source", {
      params: params,
    });
  },
  getLandingTraffic(params: any) {
    return instance.get("landings/analytics/landing-traffic", {
      params,
      headers: getAuthHeaders(),
    });
  },
  getSiteTraffic(params: any) {
    return instance.get("landings/analytics/site-traffic", {
      params,
      headers: getAuthHeaders(),
    });
  },
  getAdListQuarantine(params: any) {
    return instance.get("ad_control/ads/quarantine", {
      params,
      headers: getAuthHeaders(),
    });
  },
  getAdListObservation(params: any) {
    return instance.get("ad_control/ads/observation", {
      params,
      headers: getAuthHeaders(),
    });
  },
  getAdStaffList() {
    return instance.get("ad_control/ads/staff", {
      headers: getAuthHeaders(),
    });
  },
  updateAdStaff({ id, name }: { id: number; name: string }) {
    return instance.put(
      `ad_control/ads/staff/${id}`,
      { name },
      { headers: getAuthHeaders() },
    );
  },
  deleteAdStaff(id: number) {
    return instance.delete(`ad_control/ads/staff/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  createAdStaff(name: string) {
    return instance.post(
      "ad_control/ads/staff",
      { name },
      { headers: getAuthHeaders() },
    );
  },
  getAdAccountsList() {
    return instance.get("ad_control/ads/accounts", {
      headers: getAuthHeaders(),
    });
  },
  updateAdAccount({ id, name }: { id: number; name: string }) {
    return instance.put(
      `ad_control/ads/accounts/${id}`,
      { name },
      { headers: getAuthHeaders() },
    );
  },
  deleteAdAccount(id: number) {
    return instance.delete(`ad_control/ads/accounts/${id}`, {
      headers: getAuthHeaders(),
    });
  },
  createAdAccount(name: string) {
    return instance.post(
      "ad_control/ads/accounts",
      { name },
      {
        headers: getAuthHeaders(),
      },
    );
  },
  getAdLandingAssigned(id: string) {
    return instance.get(`ad_control/ads/landing/${id}/assignment`, {
      headers: getAuthHeaders(),
    });
  },
  putAdLandingAssigned(
    id: string,
    data: { staff_id: number | null; account_id: number | null },
  ) {
    return instance.put(`ad_control/ads/landing/${id}/assignment`, data, {
      headers: getAuthHeaders(),
    });
  },
};
