export interface CartItemType {
  id: number;
  landing_name: string;
  authors: any[];
  page_name: string;
  old_price: number;
  new_price: number;
  preview_photo: string;
  course_ids: number[];
}

export interface CartType {
  items: CartItemType[];
  quantity: number;
  loading?: boolean;
}
