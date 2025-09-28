import s from "./CategoriesFilter.module.scss";
import ExtendedToggleButton from "../../../../components/ui/ExtendedToggleButton/ExtendedToggleButton.tsx";
import {
  SearchResultKeysType,
  SearchResultsType,
} from "../../../../store/slices/mainSlice.ts";
import { useSearchParams } from "react-router-dom";

const CategoriesFilter = ({
  resultKeys,
  selectedCategories,
  loading,
  searchResults,
  urlKey,
  isBtnDisabled,
}: {
  resultKeys: SearchResultKeysType[];
  selectedCategories: SearchResultKeysType[];
  loading: boolean;
  searchResults: SearchResultsType;
  urlKey: string;
  isBtnDisabled: boolean;
}) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const handleClick = (key: SearchResultKeysType) => {
    let newValue: SearchResultKeysType[];
    if (selectedCategories.includes(key)) {
      if (selectedCategories.length > 1) {
        newValue = selectedCategories.filter((l) => l !== key);
      } else {
        newValue = selectedCategories;
      }
    } else {
      newValue = [...selectedCategories, key];
    }
    searchParams.delete(urlKey);
    newValue.forEach((key) => searchParams.append(urlKey, key));
    setSearchParams(searchParams, { replace: true });
  };

  return (
    <div className={s.toggle_btns_list}>
      {resultKeys.map((key) => {
        const isActive = selectedCategories.includes(key);
        const isLastActive = isActive && selectedCategories.length === 1;

        return (
          <ExtendedToggleButton
            handleClick={() => handleClick(key)}
            isClickable={!loading}
            isActive={isActive}
            key={key}
            loading={loading}
            isLastActive={isLastActive}
            transKey={`search.results.${key}`}
            isDisabled={isBtnDisabled}
            num={searchResults?.counts[key] ?? undefined}
          />
        );
      })}
    </div>
  );
};

export default CategoriesFilter;
