export interface CartApiResponse {
  items: CartApiItemResponse[];
  current_discount: number;
  next_discount: number;
  total_amount: number;
  total_amount_with_balance_discount: number;
  total_new_amount: number;
  total_old_amount: number;
}

export interface CartApiItemResponse {
  id: number;
  item_type: CartItemKind;
  landing: CartItemCourseType | null;
  book: CartItemBookType | null;
}

export interface CartItemCourseType {
  id: number;
  landing_name: string;
  authors: any[];
  page_name: string;
  old_price: number;
  new_price: number;
  preview_photo: string;
  course_ids: number[];
  lessons_count?: string;
}

export interface CartItemBookType {
  id: number;
  landing_name: string;
  authors: any[];
  page_name: string;
  old_price: number;
  new_price: number;
  preview_photo: string;
  book_ids: number[];
}

export type CartItemKind = "LANDING" | "BOOK";

export interface CartItemType {
  data: CartItemBookType | CartItemCourseType;
  item_type: CartItemKind;
}

export interface CartType {
  items: CartItemType[];
  quantity: number;
  loading?: boolean;
  current_discount: number;
  next_discount: number;
  total_amount: number;
  total_amount_with_balance_discount: number;
  total_new_amount: number;
  total_old_amount: number;
}
