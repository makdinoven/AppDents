import { LanguagesType } from "../../components/ui/LangLogo/LangLogo.tsx";
import { BookFormat } from "../../common/helpers/commonConstants.ts";

export type BookCardsParams = {
  language?: LanguagesType;
  tags?: string[];
  formats?: BookFormat[];
  publisher_ids?: string[] | number[];
  author_ids?: string[] | number[];
  year_from?: string;
  year_to?: string;
  price_from?: string;
  price_to?: string;
  pages_from?: string;
  pages_to?: string;
  q?: string;

  //sort
  sort?:
    | "price_asc"
    | "price_desc"
    | "pages_asc"
    | "pages_desc"
    | "year_asc"
    | "year_desc"
    | "new_asc"
    | "new_desc"
    | "popular_asc"
    | "popular_desc";

  //meta
  include_filters?: boolean;

  //pagination
  page?: number;
  size?: number;
};

export type MultiSelectOption = {
  id: number | null;
  value: string | null;
  name: string;
  count: number;
};

export type RangeFilter = {
  type: "range";
  label: string;
  param_name_from: string;
  param_name_to: string;
  min: number;
  max: number;
  unit: string;
};

export type SortOption = {
  value: string;
  label: string;
};

export type Filter = MultiSelectFilter | RangeFilter;

export type FiltersMap = Record<string, Filter>;

export type FiltersResponse = {
  filters: FiltersMap;
  available_sorts: SortOption[];
};

export type MultiSelectFilter = {
  type: "multiselect";
  label: string;
  param_name: string;
  options: MultiSelectOption[];
  has_more: boolean;
  total_count: number;
  search_endpoint: string | null;
};

export type EntityListResponse = {
  total: number;
  total_pages: number;
  page: number;
  size: number;
  cards: any[];
  filters: FiltersResponse;
};
