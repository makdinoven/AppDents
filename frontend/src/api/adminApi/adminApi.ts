import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";

export const adminApi = {
  getCoursesList() {
    try {
      return instance.get("courses/list?skip=0&limit=500", {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getCourse(id: any) {
    return instance.get(`courses/detail/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  createCourse(data: any) {
    try {
      return instance.post(`courses/`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  deleteCourse(id: any) {
    try {
      return instance.delete(`courses/${id}`, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  updateCourse(id: any, data: any) {
    try {
      return instance.put(`courses/${id}`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getLandingsList() {
    try {
      return instance.get("landings/list?skip=0&limit=500", {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getLanding(id: any) {
    return instance.get(`landings/detail/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  createLanding(data: any) {
    try {
      return instance.post(`landings/`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  deleteLanding(id: any) {
    try {
      return instance.delete(`landings/${id}`, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  updateLanding(id: any, data: any) {
    try {
      return instance.put(`landings/${id}`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getUsers() {
    try {
      return instance.get("users/", { headers: getAuthHeaders() });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getAuthors() {
    try {
      return instance.get("authors/");
    } catch (error) {
      return Promise.reject(error);
    }
  },
};
