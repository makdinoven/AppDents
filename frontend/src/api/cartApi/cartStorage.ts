import { CartItemType, CartType } from "./types";

const CART_KEY = "DENTS_CART";

const getInitialCart = (): CartType => ({
  items: [],
  quantity: 0,
});

export const cartStorage = {
  getCart(): CartType {
    if (typeof window === "undefined") return getInitialCart();
    try {
      const raw = localStorage.getItem(CART_KEY);
      const parsed = raw ? JSON.parse(raw) : getInitialCart();
      return {
        items: parsed.items || [],
        quantity: (parsed.items || []).length,
      };
    } catch (err) {
      console.error("Failed to parse cart:", err);
      return getInitialCart();
    }
  },

  hasItem(itemId: number): boolean {
    const cart = this.getCart();
    return cart.items.some((item) => item.id === itemId);
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

    if (cart.items.find((i) => i.id === item.id)) return;

    const updatedItems = [...cart.items, item];
    this.setCart({ items: updatedItems, quantity: updatedItems.length });
  },

  removeItem(itemId: number): void {
    const cart = this.getCart();
    const updatedItems = cart.items.filter((item) => item.id !== itemId);
    this.setCart({ items: updatedItems, quantity: updatedItems.length });
  },
};
