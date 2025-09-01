import s from "./SearchPage.module.scss";
import Search from "../../components/ui/Search/Search.tsx";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../common/hooks/useOutsideClick.ts";
import { useSearchParams } from "react-router-dom";
import { Trans } from "react-i18next";
import ModalCloseButton from "../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import useDebounce from "../../common/hooks/useDebounce.ts";
import ModalOverlay from "../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import ResultList from "./content/ResultsList/ResultsList.tsx";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import LoaderOverlay from "../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import { LANGUAGES } from "../../common/helpers/commonConstants.ts";
import LangLogo, {
  LanguagesType,
} from "../../components/ui/LangLogo/LangLogo.tsx";
import NoResults from "../../components/ui/NoResults/NoResults.tsx";
import ExtendedToggleButton from "../../components/ui/ExtendedToggleButton/ExtendedToggleButton.tsx";
import { globalSearch } from "../../store/actions/mainActions.ts";
import {
  clearSearch,
  SearchResultsType,
} from "../../store/slices/mainSlice.ts";

const RESULT_KEYS: (keyof Omit<Exclude<SearchResultsType, null>, "counts">)[] =
  [
    "landings",
    "authors",
    // "book_landings",
  ];

// type ResultKey = keyof Omit<SearchResults, "counts">;

const SearchPage = () => {
  const SEARCH_KEY = "q";
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const dispatch = useDispatch<AppDispatchType>();
  const { loading, q } = useSelector(
    (state: AppRootStateType) => state.main.search,
  );
  const selectedLanguagesFromStore = useSelector(
    (state: AppRootStateType) => state.main.search.selectedLanguages,
  );
  const selectedResultTypesFromStore = useSelector(
    (state: AppRootStateType) => state.main.search.selectedResultTypes,
  );
  const searchResults = useSelector(
    (state: AppRootStateType) => state.main.search.results,
  );
  const [searchParams] = useSearchParams();
  const closeModalRef = useRef<() => void>(null);
  const [selectedLanguages, setSelectedLanguages] = useState(
    selectedLanguagesFromStore ?? [language],
  );
  const [selectedResultTypes, setSelectedResultTypes] = useState(
    selectedResultTypesFromStore ?? RESULT_KEYS,
  );
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  useOutsideClick(wrapperRef, () => {
    handleClose();
  });
  const inputRef = useRef<HTMLInputElement | null>(null);
  const searchValue = searchParams.get(SEARCH_KEY);
  const debouncedSearchValue = useDebounce(searchValue, 300);
  const hasResults =
    searchResults &&
    RESULT_KEYS.some(
      (key) => searchResults[key] && searchResults[key]!.length > 0,
    );
  const showNoResults = !hasResults && !loading;

  useEffect(() => {
    if (
      debouncedSearchValue === q &&
      hasResults &&
      selectedLanguagesFromStore !== selectedLanguagesFromStore &&
      selectedResultTypesFromStore !== selectedResultTypes
    ) {
      return;
    }

    if (debouncedSearchValue) {
      dispatch(
        globalSearch({
          q: debouncedSearchValue.trim(),
          languages: selectedLanguages,
          types: selectedResultTypes,
        }),
      );
    } else if (hasResults) {
      dispatch(clearSearch());
      // setTotalResults(0);
    }
  }, [debouncedSearchValue, selectedLanguages, selectedResultTypes]);

  // useEffect(() => {
  //   console.log(searchResults);
  // }, [searchResults]);

  const handleClose = () => {
    dispatch(clearSearch());
    closeModalRef.current?.();
  };

  const handleSelect = <T,>(
    item: T,
    setSelected: React.Dispatch<React.SetStateAction<T[]>>,
  ) => {
    setSelected((prev) => {
      if (prev.includes(item)) {
        if (prev.length === 1) {
          return prev;
        }
        return prev.filter((p) => p !== item);
      } else {
        return [...prev, item];
      }
    });
  };

  return (
    <ModalOverlay
      isVisibleCondition={true}
      isUsedAsPage
      modalPosition={"top"}
      onInitClose={(fn) => (closeModalRef.current = fn)}
    >
      <div ref={wrapperRef} className={s.modal}>
        <div className={s.modal_content}>
          <div className={s.modal_header}>
            <ModalCloseButton
              className={s.close_button}
              onClick={handleClose}
            />
            <h3 className={s.dropdown_title}>
              <Trans i18nKey={"nav.search"} />
            </h3>
          </div>

          <div className={s.search_body}>
            <div className={s.search_wrapper}>
              <Search
                inputRef={inputRef}
                id={SEARCH_KEY}
                placeholder={"search.searchPlaceholder"}
              />

              {/*<p*/}
              {/*  style={{ opacity: `${totalResults > 0 ? 1 : 0.7}` }}*/}
              {/*  className={s.search_results}*/}
              {/*>*/}
              {/*  <Trans i18nKey={"search.result"} count={totalResults} />*/}
              {/*</p>*/}
            </div>
          </div>
          <div className={s.search_filters}>
            <div className={s.toggle_btns_list}>
              {/*<p>*/}
              {/*  <Trans i18nKey={"search.results.results"} />*/}
              {/*</p>*/}
              {RESULT_KEYS.map((key) => {
                const isActive = selectedResultTypes.includes(key);
                const isLastActive =
                  isActive && selectedResultTypes.length === 1;
                const isDisabled = !searchResults;

                return (
                  <ExtendedToggleButton
                    handleClick={() =>
                      handleSelect(key, setSelectedResultTypes)
                    }
                    isActive={isActive}
                    key={key}
                    isLastActive={isLastActive}
                    isDisabled={isDisabled}
                    transKey={`search.results.${key}`}
                    num={searchResults?.counts[key] ?? undefined}
                  />
                );
              })}
            </div>

            <ul className={s.languages_list}>
              {LANGUAGES.map((lang) => (
                <li key={lang.value}>
                  <LangLogo
                    isChecked={selectedLanguages.includes(lang.value)}
                    isHoverable
                    className={s.lang_logo}
                    lang={lang.value as LanguagesType}
                    onClick={() =>
                      !loading && handleSelect(lang.value, setSelectedLanguages)
                    }
                  />
                </li>
              ))}
            </ul>
          </div>
          <div className={s.results_container}>
            {hasResults && (
              <div className={s.results_list}>
                {loading && <LoaderOverlay />}
                {RESULT_KEYS.map((key) => {
                  const data = searchResults[key];
                  const quantity = searchResults.counts[key];
                  if (!data || data.length === 0) return null;

                  return (
                    <ResultList
                      key={key}
                      type={key}
                      data={data}
                      quantity={quantity}
                    />
                  );
                })}
              </div>
            )}
            {showNoResults && <NoResults />}
          </div>
        </div>
      </div>
    </ModalOverlay>
  );
};

export default SearchPage;
