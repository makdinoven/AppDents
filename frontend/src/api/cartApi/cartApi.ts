import { instance } from "../api-instance.ts";
import { getAuthHeaders } from "../../common/helpers/helpers.tsx";

export const cartApi = {
  getCart() {
    return instance.get("cart", { headers: getAuthHeaders() });
  },
  addCartItem(id: number) {
    try {
      return instance.post(
        `cart/landing/${id}`,
        {},
        { headers: getAuthHeaders() },
      );
    } catch (error) {
      console.log(error);
    }
  },
  removeCartItem(id: number) {
    return instance.delete(`cart/landing/${id}`, { headers: getAuthHeaders() });
  },

  previewCart(data: { landing_ids: number[] }) {
    return instance.post(`cart/preview`, data);
  },
};
