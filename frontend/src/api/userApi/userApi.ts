import { instance } from "../api-instance.ts";
import { ChangePasswordType, LoginType, SignUpType } from "./types.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";

export const userApi = {
  getMe() {
    return instance.get("users/me", { headers: getAuthHeaders() });
  },

  changePassword(data: ChangePasswordType) {
    return instance.post(`users/forgot-password`, {
      data: data,
      headers: getAuthHeaders(),
    });
  },

  resetPassword(newPassword: any, id: number) {
    return instance.put(`users/${id}/password`, newPassword, {
      headers: getAuthHeaders(),
    });
  },

  signUp(data: SignUpType) {
    return instance.post(`users/register`, data);
  },

  login(data: LoginType) {
    const params = new URLSearchParams();
    params.append("grant_type", "password");
    params.append("username", data.email);
    params.append("password", data.password);
    params.append("scope", "");
    params.append("client_id", "string");
    params.append("client_secret", "string");

    return instance.post("users/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  getCourses() {
    return instance.get("users/me/courses", {
      headers: getAuthHeaders(),
    });
  },
};
