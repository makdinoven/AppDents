import { CartItemKind, CartItemType, CartType } from "./types.ts";

const CART_KEY = "DENTS_CART_NEW";

export function getInitialCart(): CartType {
  return {
    items: [],
    quantity: 0,
    loading: false,
    current_discount: 0,
    next_discount: 0,
    total_amount: 0,
    total_amount_with_balance_discount: 0,
    total_new_amount: 0,
    total_old_amount: 0,
  };
}

export const cartStorage = {
  getCart(): CartType {
    if (typeof window === "undefined") return getInitialCart();

    try {
      const raw = localStorage.getItem(CART_KEY);
      if (!raw) return getInitialCart();

      const parsed = JSON.parse(raw);

      return {
        items: parsed.items ?? [],
        quantity: parsed.quantity ?? 0,
        loading: false,
        current_discount: parsed.current_discount ?? 0,
        next_discount: parsed.next_discount ?? 0,
        total_amount: parsed.total_amount ?? 0,
        total_amount_with_balance_discount:
          parsed.total_amount_with_balance_discount ?? 0,
        total_new_amount: parsed.total_new_amount ?? 0,
        total_old_amount: parsed.total_old_amount ?? 0,
      };
    } catch (err) {
      console.error("Failed to parse cart:", err);
      return getInitialCart();
    }
  },

  getLandingIds(): {
    cart_landing_ids: number[];
    cart_book_landing_ids: number[];
  } {
    const cart = this.getCart();
    const result = {
      cart_landing_ids: [] as number[],
      cart_book_landing_ids: [] as number[],
    };
    for (const item of cart.items) {
      if (item.item_type === "LANDING") {
        result.cart_landing_ids.push(item.data.id);
      } else if (item.item_type === "BOOK") {
        result.cart_book_landing_ids.push(item.data.id);
      }
    }

    if (
      result.cart_landing_ids.length === 0 &&
      result.cart_book_landing_ids.length === 0
    ) {
      return { cart_landing_ids: [], cart_book_landing_ids: [] };
    }

    return result;
  },

  setCart(cart: CartType): void {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
    } catch (err) {
      console.error("Failed to save cart:", err);
    }
  },

  clearCart(): void {
    localStorage.removeItem(CART_KEY);
  },

  addItem(item: CartItemType): void {
    const cart = this.getCart();
    if (cart.items.find((i) => i.data.id === item.data.id)) return;
    const updatedItems = [...cart.items, item];

    this.setCart({
      ...cart,
      items: updatedItems,
      quantity: updatedItems.length,
    });
  },

  removeItem(item_type: CartItemKind, itemId: number): void {
    const cart = this.getCart();

    const updatedItems = cart.items.filter(
      (item) => !(item.item_type === item_type && item.data.id === itemId),
    );

    this.setCart({
      ...cart,
      items: updatedItems,
      quantity: updatedItems.length,
    });
  },
};
