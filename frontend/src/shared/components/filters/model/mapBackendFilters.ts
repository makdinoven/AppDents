import {
  Filter,
  FiltersDataUI,
  SelectedUI,
  UIMultiselectOption,
} from "./types.ts";

const SELECTED_KEY_TO_PARAM: Record<string, string> = {
  publishers: "publisher_ids",
  authors: "author_ids",
  tags: "tags",
  formats: "formats",
};

export function mapBackendFilters(raw: any): FiltersDataUI {
  const filters: Filter[] = [];

  Object.values(raw.filters).forEach((f: any) => {
    if (f.type === "multiselect") {
      filters.push({
        type: "multiselect",
        label: `filters.keys.${f.param_name.toLowerCase()}`,
        name: f.param_name,
        has_more: f.has_more,
        endpoint: f.search_endpoint,
        options: mapBackendFilterOptions(f.options),
      });
    }

    if (f.type === "range") {
      filters.push({
        type: "range",
        label: `filters.keys.range.${f.unit.toLowerCase()}`,
        from: f.param_name_from,
        to: f.param_name_to,
        min: f.min,
        max: f.max,
        unit: `filters.keys.range.unit.${f.unit.toLowerCase()}`,
      });
    }
  });

  return {
    filters,
    sorts:
      raw.available_sorts?.map((sort: any) => ({
        value: sort.value,
        label: `sort.keys.${sort.value.toLowerCase()}`,
      })) ?? [],
  };
}

export function mapBackendSelected(selectedRaw: any): SelectedUI[] {
  const selected: SelectedUI[] = [];
  if (!selectedRaw) return selected;

  Object.entries(selectedRaw).forEach(([key, data]: [string, any]) => {
    if (!data) return;

    // 1) multiselect: publishers/authors/tags/formats
    if ("options" in data && Array.isArray(data.options)) {
      const paramName = SELECTED_KEY_TO_PARAM[key];
      if (!paramName) return;

      data.options.forEach((opt: any) => {
        selected.push({
          kind: "multiselect",
          name: opt.name,
          value: String(opt.id ?? opt.value),
          paramName,
        });
      });

      return;
    }

    if ("value_from" in data || "value_to" in data) {
      const from = data.value_from;
      const to = data.value_to;

      if (from == null && to == null) return;

      selected.push({
        kind: "range",
        from,
        to,
        paramName: key,
      });
    }
  });

  return selected;
}

export function mapBackendFilterOption(o: any): UIMultiselectOption {
  return {
    value: String(o.id ?? o.value ?? ""),
    label: o.name ?? String(o.value ?? o.id ?? ""),
    count: o.count,
  };
}

export function mapBackendFilterOptions(list: any[]): UIMultiselectOption[] {
  return list.map(mapBackendFilterOption);
}
