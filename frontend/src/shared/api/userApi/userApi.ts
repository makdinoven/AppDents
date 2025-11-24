import { instance } from "../api-instance.ts";
import { ChangePasswordType, SignUpType } from "./types.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";
import { REF_CODE_LS_KEY } from "../../common/helpers/commonConstants.ts";
import { cartStorage } from "../cartApi/cartStorage.ts";

export const userApi = {
  getMe() {
    return instance.get("users/me", { headers: getAuthHeaders() });
  },

  forgotPassword(data: ChangePasswordType, language: string) {
    return instance.post(`users/forgot-password`, data, {
      params: {
        region: language,
      },
    });
  },

  resetPassword(newPassword: any, id: number) {
    return instance.put(`users/${id}/password`, newPassword, {
      headers: getAuthHeaders(),
    });
  },

  signUp(data: SignUpType, language: string) {
    const rcCode = localStorage.getItem(REF_CODE_LS_KEY);
    const cartLandingIds = cartStorage.getLandingIds();

    return instance.post(`users/register`, data, {
      params: {
        region: language,
        ...(rcCode && { ref: rcCode }),
        ...(cartLandingIds && {
          transfer_cart: true,
          cart_landing_ids: cartLandingIds.cart_landing_ids.join(","),
          cart_book_landing_ids: cartLandingIds.cart_book_landing_ids.join(","),
        }),
      },
    });
  },

  getRefLink() {
    return instance.get(`wallet/referral-link`, { headers: getAuthHeaders() });
  },

  login(data: any) {
    const params = new URLSearchParams();
    params.append("grant_type", "password");
    params.append("username", data.email);
    params.append("password", data.password);
    params.append("scope", "");
    params.append("client_id", "string");
    params.append("client_secret", "string");

    const cartLandingIds = cartStorage.getLandingIds();

    if (cartLandingIds) {
      params.append("transfer_cart", "true");
      params.append(
        "cart_landing_ids",
        cartLandingIds.cart_landing_ids.join(","),
      );
      params.append(
        "cart_book_landing_ids",
        cartLandingIds.cart_book_landing_ids.join(","),
      );
    }

    return instance.post("users/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  getCourses() {
    return instance.get("users/me/courses", {
      headers: getAuthHeaders(),
    });
  },

  getBooks() {
    return instance.get("users/me/books", {
      headers: getAuthHeaders(),
    });
  },

  getMyReferrals() {
    return instance.get("wallet/referrals", { headers: getAuthHeaders() });
  },

  getMyTransactions() {
    return instance.get("wallet/transactions", {
      headers: getAuthHeaders(),
    });
  },

  checkEmail(params: { email: string }) {
    return instance.post("validations/check-email", params);
  },

  inviteFriend(data: { recipient_email: string; language: string }) {
    return instance.post("wallet/send-invitation", data, {
      headers: getAuthHeaders(),
    });
  },

  requestProduct(data: { user_id: number; text: string }) {
    return instance.post("request/course-request", data);
  },
};
