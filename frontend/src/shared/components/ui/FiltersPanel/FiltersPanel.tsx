import { Fragment, useEffect } from "react";
import MultiSelect from "../../MultiSelect/MultiSelect.tsx";
import {
  FILTER_PARAM_KEYS,
  FilterKeys,
  LANGUAGES_NAME,
  PAGE_SIZES,
  PAGE_SIZES_ALTERNATE,
  SORT_FILTERS,
} from "../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams } from "react-router-dom";
import { getTags } from "../../../store/actions/mainActions.ts";
import s from "./FiltersPanel.module.scss";

type FiltersPanelProps = {
  filters: FilterKeys[];
  defaultSize: number;
};

const FiltersPanel = ({ filters, defaultSize }: FiltersPanelProps) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const dispatch = useDispatch<any>();
  const tagsOptions = useSelector((state: any) => state.main.tags);

  useEffect(() => {
    if (tagsOptions.length < 1) {
      dispatch(getTags());
    }
  }, [dispatch, tagsOptions.length]);

  const currentFilters: Record<FilterKeys, string> = {
    tags: searchParams.get(FILTER_PARAM_KEYS.tags) || "all",
    sort: searchParams.get(FILTER_PARAM_KEYS.sort) || "popular",
    size: searchParams.get(FILTER_PARAM_KEYS.size) || defaultSize.toString(),
    language: searchParams.get(FILTER_PARAM_KEYS.language) || "all",
  };

  const filterConfig: Record<
    FilterKeys,
    {
      options: Array<{ value: string; name: string }>;
      defaultValue: string;
    }
  > = {
    tags: {
      options: tagsOptions,
      defaultValue: "all",
    },
    sort: {
      options: SORT_FILTERS.filter((item) => item.value !== "recommend"),
      defaultValue: "popular",
    },
    size: {
      options: defaultSize === 12 ? PAGE_SIZES_ALTERNATE : PAGE_SIZES,
      defaultValue: defaultSize.toString(),
    },
    language: {
      options: LANGUAGES_NAME,
      defaultValue: "all",
    },
  };

  const updateParam = (paramKey: string, value: string | number | null) => {
    const newParams = new URLSearchParams(searchParams);
    if (value === null || (typeof value === "string" && value === "all")) {
      newParams.delete(paramKey);
    } else {
      newParams.set(paramKey, String(value));
    }
    setSearchParams(newParams, { replace: true });
  };

  const commonFilterProps = {
    isSearchable: false,
    placeholder: "",
    isMultiple: false,
    valueKey: "value" as const,
    labelKey: "name" as const,
  };

  return (
    <div className={s.filters}>
      {filters.map((key) => {
        const paramName = FILTER_PARAM_KEYS[key];
        const { options } = filterConfig[key];
        const selectedValue = currentFilters[key];
        return (
          <Fragment key={key}>
            <MultiSelect
              {...commonFilterProps}
              options={options}
              id={paramName}
              selectedValue={selectedValue}
              onChange={(e) => updateParam(paramName, e.value as string)}
            />
          </Fragment>
        );
      })}
    </div>
  );
};

export default FiltersPanel;
