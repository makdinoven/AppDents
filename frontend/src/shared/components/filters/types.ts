export type SortOption = {
  value: string;
  label: string;
};

export type MultiselectOption = {
  id: number | null;
  value: string | null;
  name: string;
  count: number;
};

export type MultiselectFilter = {
  type: "multiselect";
  label: string;
  param_name: string;
  options: MultiselectOption[];
  has_more: boolean;
  total_count: number;
  search_endpoint: string | null;
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

export type Filter = MultiselectFilter | RangeFilter;

export type FiltersData = {
  filters: Record<string, Filter>;
  available_sorts: SortOption[];
};
