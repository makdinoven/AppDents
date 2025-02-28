import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";

export const adminApi = {
  getCoursesList() {
    try {
      return instance.get("courses/", { headers: getAuthHeaders() });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  getCourse(id: any) {
    return instance.get(`courses/full/${id}`);
  },

  createCourse(data: any) {
    try {
      return instance.post(`courses/full`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  deleteCourse(id: any) {
    try {
      return instance.delete(`courses/full/${id}`, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  updateCourse(id: any, data: any) {
    try {
      return instance.put(`courses/full/${id}`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  addCourseSection(id: any, data: any) {
    try {
      return instance.post(`courses/${id}/sections`, data, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  addCourseModule(courseId: any, sectionId: any, data: any) {
    try {
      return instance.post(
        `courses/${courseId}/sections/${sectionId}/modules`,
        data,
        {
          headers: getAuthHeaders(),
        },
      );
    } catch (error) {
      return Promise.reject(error);
    }
  },

  deleteCourseSection(courseId: any, sectionId: any) {
    try {
      return instance.delete(`courses/${courseId}/sections/${sectionId}`, {
        headers: getAuthHeaders(),
      });
    } catch (error) {
      return Promise.reject(error);
    }
  },

  deleteCourseModule(courseId: any, sectionId: any, moduleId: any) {
    try {
      return instance.delete(
        `courses/${courseId}/sections/${sectionId}/modules/${moduleId}`,
        {
          headers: getAuthHeaders(),
        },
      );
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
      return instance.get("authors/list");
    } catch (error) {
      return Promise.reject(error);
    }
  },
};
