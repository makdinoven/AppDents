import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";

export const adminApi = {
  getCoursesList() {
    return instance.get("courses/list?size=1000", {
      headers: getAuthHeaders(),
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

  getLandingsList() {
    return instance.get("landings/list?size=1000", {
      headers: getAuthHeaders(),
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

  getAuthorsList() {
    return instance.get("authors/?size=1000");
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

  getUsersList() {
    return instance.get("users/admin/users?size=100000", {
      headers: getAuthHeaders(),
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

  uploadPhoto(file: any) {
    return instance.post("photo/photo", file);
  },

  getMostPopularLandings(params: any) {
    return instance.get("landings/most-popular", { params: params });
  },
  getLanguageStats(params: any) {
    return instance.get("landings/analytics/language-stats", {
      params: params,
    });
  },
};
