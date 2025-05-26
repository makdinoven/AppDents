import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.ts";

export const cartApi = {
  getCart(data: any) {
    console.log(data);
    return instance.get("users/me", { headers: getAuthHeaders() });
  },
  addCartItem(data: any) {
    console.log(data);
    return instance.get("users/me", { headers: getAuthHeaders() });
  },
  removeCartItem(data: any) {
    console.log(data);
    return instance.get("users/me", { headers: getAuthHeaders() });
  },
};
