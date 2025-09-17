import s from "./CategoriesFilter.module.scss";
import ExtendedToggleButton from "../../../../components/ui/ExtendedToggleButton/ExtendedToggleButton.tsx";
import {
  SearchResultKeysType,
  SearchResultsType,
} from "../../../../store/slices/mainSlice.ts";
import { useSearchParams } from "react-router-dom";

const CategoriesFilter = ({
  resultKeys,
  selectedResultTypes,
  loading,
  searchResults,
  urlKey,
}: {
  resultKeys: SearchResultKeysType[];
  selectedResultTypes: SearchResultKeysType[];
  loading: boolean;
  searchResults: SearchResultsType;
  urlKey: string;
}) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const handleClick = (key: SearchResultKeysType) => {
    let newValue: SearchResultKeysType[];
    if (selectedResultTypes.includes(key)) {
      if (selectedResultTypes.length > 1) {
        newValue = selectedResultTypes.filter((l) => l !== key);
      } else {
        newValue = selectedResultTypes;
      }
    } else {
      newValue = [...selectedResultTypes, key];
    }
    searchParams.delete(urlKey);
    newValue.forEach((key) => searchParams.append(urlKey, key));
    setSearchParams(searchParams, { replace: true });
  };

  return (
    <div className={s.toggle_btns_list}>
      {resultKeys.map((key) => {
        const isActive = selectedResultTypes.includes(key);
        const isLastActive = isActive && selectedResultTypes.length === 1;

        return (
          <ExtendedToggleButton
            handleClick={() => handleClick(key)}
            isClickable={!loading}
            isActive={isActive}
            key={key}
            loading={loading}
            isLastActive={isLastActive}
            transKey={`search.results.${key}`}
            num={searchResults?.counts[key] ?? undefined}
          />
        );
      })}
    </div>
  );
};

export default CategoriesFilter;
