import { instance } from "../api-instance.ts";
import { ChangePasswordType, LoginType, SignUpType } from "./types.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";

export const userApi = {
  getMe() {
    try {
      return instance.get("users/me", { headers: getAuthHeaders() });
    } catch (error) {
      return Promise.reject(error);
    }
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

  changePassword(data: ChangePasswordType) {
    return instance.post(`users/forgot-password`, data);
  },
};
