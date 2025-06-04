import { CartItemType, CartTypeExtended } from "./types";

const CART_KEY = "DENTS_CART";

export function getInitialCart(): CartTypeExtended {
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
  getCart(): CartTypeExtended {
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

  getLandingIds(): number[] {
    const cart = this.getCart();
    return cart.items.map((item) => item.landing.id);
  },

  setCart(cart: CartTypeExtended): void {
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
    if (cart.items.find((i) => i.landing.id === item.landing.id)) return;
    const updatedItems = [...cart.items, item];

    this.setCart({
      ...cart,
      items: updatedItems,
      quantity: updatedItems.length,
    });
  },

  removeItem(itemId: number): void {
    const cart = this.getCart();

    const updatedItems = cart.items.filter(
      (item) => item.landing.id !== itemId,
    );

    this.setCart({
      ...cart,
      items: updatedItems,
      quantity: updatedItems.length,
    });
  },
};
