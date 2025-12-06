import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";

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
  has_more: boolean;
  endpoint: string;
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

export type SelectedFilterOptionBackend = {
  id: number | null;
  value: string | null;
  name: string;
  count?: number;
};

export type SelectedFilterBackendEntry = {
  options: SelectedFilterOptionBackend[];
} | null;

export type SelectedFiltersBackend = {
  [paramName: string]: SelectedFilterBackendEntry;
};

export type Filter = UIMultiselectFilter | UIRangeFilter;

export type FiltersDataUI = {
  filters: Filter[];
  sorts: UISortOption[];
};

export type SelectedUI =
  | {
      kind: "multiselect";
      name: string;
      value: string;
      paramName: string;
    }
  | {
      kind: "range";
      from?: number;
      to?: number;
      paramName: string;
    };

export type SetActionType = (next: Partial<ListQueryParams>) => void;
export type ResetActionType = (key: string) => void;
export type ResetAllActionType = () => void;
export type ResetSingleActionType = (paramName: string, value?: string) => void;

export type FilterActionsType = {
  set: SetActionType;
  reset: ResetActionType;
  resetAll: ResetAllActionType;
  resetSingle: ResetSingleActionType;
};
