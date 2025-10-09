export interface CartApiResponse {
  items: CartItemType[];
  current_discount: number;
  next_discount: number;
  total_amount: number;
  total_amount_with_balance_discount: number;
  total_new_amount: number;
  total_old_amount: number;
}

export interface CartTypeExtended extends CartApiResponse {
  quantity: number;
  loading: boolean;
}

export interface CartLandingType {
  id: number;
  landing_name: string;
  authors: any[];
  page_name: string;
  old_price: number;
  new_price: number;
  preview_photo: string;
  course_ids: number[];
}

export interface CartItemType {
  landing: CartLandingType;
  item_type: "LANDING" | "BOOK";
}

export interface CartType {
  items: CartItemType[];
  quantity: number;
  loading?: boolean;
}
