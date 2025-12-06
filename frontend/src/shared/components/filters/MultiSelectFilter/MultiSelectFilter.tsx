import { UIMultiselectFilter } from "../model/types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import s from "./MultiSelectFilter.module.scss";
import Option from "../../ui/Select/Option.tsx";
import { SearchIcon } from "../../../assets/icons";
import { useEffect, useState } from "react";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";
import axios from "axios";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import { BASE_URL } from "../../../common/helpers/commonConstants.ts";
import { t } from "i18next";
import { mapBackendFilterOptions } from "../model/mapBackendFilters.ts";
import { Trans } from "react-i18next";

type Props = {
  filter: UIMultiselectFilter;
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
  };
};

const MultiSelectFilter = ({ filter, params, actions }: Props) => {
  const raw = params[filter.name];
  const selected = Array.isArray(raw) ? raw : raw ? String(raw).split(",") : [];
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 400);
  const [remoteOptions, setRemoteOptions] = useState(filter.options);
  const [loading, setLoading] = useState(false);
  const hasSearch = debouncedSearch.trim().length > 0;

  const getOptions = async (q: string) => {
    setLoading(true);
    try {
      const res = await axios.get(`${BASE_URL}${filter.endpoint}`, {
        params: { q },
      });
      setRemoteOptions(mapBackendFilterOptions(res.data.options ?? []));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!filter.has_more || !filter.endpoint) return;

    const q = debouncedSearch.trim();
    if (!q) return;

    getOptions(q);
  }, [debouncedSearch, filter.has_more, filter.endpoint]);

  useEffect(() => {
    if (!hasSearch) {
      setRemoteOptions(filter.options);
    }
  }, [hasSearch, filter.options]);

  const visibleOptions = hasSearch ? remoteOptions : filter.options;

  const toggle = (value: string) => {
    const next = selected.includes(value)
      ? selected.filter((v) => v !== value)
      : [...selected, value];

    actions.set({
      [filter.name]: next.length ? next : undefined,
    });
  };

  return (
    <>
      {filter.has_more && filter.endpoint && (
        <div className={s.search_input}>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t(`${filter.label}.search`)}
          />
          <SearchIcon className={s.search_icon} />
        </div>
      )}

      <div className={`${s.filter_options} ${loading ? s.loading : ""}`}>
        {loading && <LoaderOverlay />}

        {visibleOptions.length === 0 && hasSearch && !loading && (
          <span className={s.nothing_found}>
            <Trans i18nKey={"nothingFound"} />
          </span>
        )}

        {visibleOptions.map((opt) => (
          <Option
            allowUncheck
            key={opt.value}
            option={opt}
            isActive={selected.includes(opt.value)}
            onChange={() => toggle(opt.value)}
          />
        ))}
      </div>
    </>
  );
};

export default MultiSelectFilter;
