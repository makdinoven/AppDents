import s from "./CategoriesFilter.module.scss";
import ExtendedToggleButton from "../../../../shared/components/ui/ExtendedToggleButton/ExtendedToggleButton.tsx";
import {
  SearchResultKeysType,
  SearchResultsType,
} from "../../../../shared/store/slices/mainSlice.ts";

const CategoriesFilter = ({
  resultKeys,
  selectedCategories,
  loading,
  searchResults,
  isBtnDisabled,
  onChange,
}: {
  resultKeys: SearchResultKeysType[];
  selectedCategories: SearchResultKeysType[];
  loading: boolean;
  searchResults: SearchResultsType;
  urlKey?: string;
  isBtnDisabled: boolean;
  onChange: (cats: SearchResultKeysType[]) => void;
}) => {
  const handleClick = (key: SearchResultKeysType) => {
    let newValue: SearchResultKeysType[];

    if (selectedCategories.includes(key)) {
      if (selectedCategories.length > 1) {
        newValue = selectedCategories.filter((k) => k !== key);
      } else {
        newValue = selectedCategories;
      }
    } else {
      newValue = [...selectedCategories, key];
    }

    onChange(newValue);
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
