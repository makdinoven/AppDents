import { Filter, FiltersDataUI } from "./types";

export function mapBackendFilters(raw: any): FiltersDataUI {
  const filters: Filter[] = [];

  Object.values(raw.filters).forEach((f: any) => {
    if (f.type === "multiselect") {
      filters.push({
        type: "multiselect",
        label: f.label,
        name: f.param_name,
        options: f.options.map((o: any) => ({
          value: String(o.id ?? o.value),
          label: o.name,
          count: o.count,
        })),
      });
    }

    if (f.type === "range") {
      filters.push({
        type: "range",
        label: f.label,
        from: f.param_name_from,
        to: f.param_name_to,
        min: f.min,
        max: f.max,
        unit: f.unit,
      });
    }
  });

  return {
    filters,
    sorts: raw.available_sorts ?? [],
  };
}
