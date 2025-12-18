import { getAuthHeaders, instance } from "@/shared/api";

export const cartApi = {
  getCart() {
    return instance.get("cart", { headers: getAuthHeaders() });
  },
  addCartItemCourse(id: number) {
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

  addCartItemBook(id: number) {
    try {
      return instance.post(
        `cart/book-landings/${id}`,
        {},
        { headers: getAuthHeaders() },
      );
    } catch (error) {
      console.log(error);
    }
  },
  removeCartItemCourse(id: number) {
    return instance.delete(`cart/landing/${id}`, { headers: getAuthHeaders() });
  },

  removeCartItemBook(id: number) {
    return instance.delete(`cart/book-landings/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  previewCart(landingIds: {
    cart_landing_ids: number[];
    cart_book_landing_ids: number[];
  }) {
    return instance.post(`cart/preview`, landingIds);
  },
};
