export type UISortOption = {
  value: string;
  label: string;
};

export type UIMultiselectOption = {
  value: string;
  label: string;
  count?: number;
};

export type UIMultiselectFilter = {
  type: "multiselect";
  label: string;
  name: string;
  options: UIMultiselectOption[];
};

export type UIRangeFilter = {
  type: "range";
  label: string;
  from: string;
  to: string;
  min: number;
  max: number;
  unit?: string;
};

export type Filter = UIMultiselectFilter | UIRangeFilter;

export type FiltersDataUI = {
  filters: Filter[];
  sorts: UISortOption[];
};
