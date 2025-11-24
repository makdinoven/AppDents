import s from "./SearchPage.module.scss";
import Search from "../../shared/components/ui/Search/Search.tsx";
import { useEffect, useMemo, useRef } from "react";
import useOutsideClick from "../../shared/common/hooks/useOutsideClick.ts";
import { useSearchParams } from "react-router-dom";
import { Trans } from "react-i18next";
import ModalCloseButton from "../../shared/components/ui/ModalCloseButton/ModalCloseButton.tsx";
import useDebounce from "../../shared/common/hooks/useDebounce.ts";
import ModalOverlay from "../../shared/components/Modals/ModalOverlay/ModalOverlay.tsx";
import ResultsList from "./content/ResultsList/ResultsList.tsx";
import { AppDispatchType, AppRootStateType } from "../../shared/store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import NoResults from "../../shared/components/ui/NoResults/NoResults.tsx";
import { globalSearch } from "../../shared/store/actions/mainActions.ts";
import {
  clearSearch,
  ResultLandingData,
  SearchResultKeysType,
} from "../../shared/store/slices/mainSlice.ts";
import LanguagesFilter from "./filters/LanguagesFilter/LanguagesFilter.tsx";
import { LanguagesType } from "../../shared/components/ui/LangLogo/LangLogo.tsx";
import {
  arraysEqual,
  mapCourseToResultLanding,
} from "../../shared/common/helpers/helpers.ts";
import CategoriesFilter from "./filters/CategoriesFilter/CategoriesFilter.tsx";
import { t } from "i18next";
import ResultsListSkeleton from "../../shared/components/ui/Skeletons/ResultsListSkeleton/ResultsListSkeleton.tsx";
import Loader from "../../shared/components/ui/Loader/Loader.tsx";

const RESULT_KEYS: SearchResultKeysType[] = [
  "landings",
  "authors",
  "book_landings",
];

const LANGS_URL_KEY = "langs";
const TYPES_URL_KEY = "types";

const SearchPage = () => {
  const SEARCH_KEY = "q";
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const dispatch = useDispatch<AppDispatchType>();
  const { loading, q } = useSelector(
    (state: AppRootStateType) => state.main.search,
  );
  const searchResults = useSelector(
    (state: AppRootStateType) => state.main.search.results,
  );
  const [searchParams] = useSearchParams();
  const closeModalRef = useRef<() => void>(null);
  const selectedLanguagesFromStore = useSelector(
    (state: AppRootStateType) => state.main.search.selectedLanguages,
  );
  const selectedCategoriesFromStore = useSelector(
    (state: AppRootStateType) => state.main.search.selectedCategories,
  );
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  useOutsideClick(wrapperRef, () => {
    handleClose();
  });
  const inputRef = useRef<HTMLInputElement | null>(null);
  const searchValue = searchParams.get(SEARCH_KEY);
  const debouncedSearchValue = useDebounce(searchValue, 400);
  const placeholderCoursesRaw = useSelector(
    (state: AppRootStateType) => state.main.courses,
  );
  const placeholderCourses: ResultLandingData[] = placeholderCoursesRaw.map(
    mapCourseToResultLanding,
  );

  const selectedLanguages = useMemo(() => {
    const langs = searchParams.getAll(LANGS_URL_KEY) as LanguagesType[];
    return langs.length > 0 ? langs : [language as LanguagesType];
  }, [searchParams]);

  const selectedCategories = useMemo(() => {
    const types = searchParams.getAll(TYPES_URL_KEY) as SearchResultKeysType[];
    return types.length > 0 ? types : RESULT_KEYS;
  }, [searchParams, language]);

  const hasResults =
    !!searchResults &&
    RESULT_KEYS.some(
      (key) => searchResults[key] && searchResults[key]!.length > 0,
    );

  const showSkeleton = loading && !!debouncedSearchValue;
  const showNoResults = !hasResults && !showSkeleton && !!debouncedSearchValue;
  const showPlaceholderCourses =
    !hasResults &&
    !showNoResults &&
    !!placeholderCourses.length &&
    !loading &&
    !debouncedSearchValue;

  useEffect(() => {
    if (
      debouncedSearchValue === q &&
      arraysEqual(selectedLanguagesFromStore!, selectedLanguages) &&
      arraysEqual(selectedCategoriesFromStore!, selectedCategories)
    ) {
      return;
    }

    if (debouncedSearchValue) {
      dispatch(
        globalSearch({
          q: debouncedSearchValue.trim(),
          languages: selectedLanguages,
          types: selectedCategories,
        }),
      );
    } else if (hasResults) {
      dispatch(clearSearch());
    }
  }, [debouncedSearchValue, selectedLanguages, selectedCategories]);

  const handleClose = () => {
    dispatch(clearSearch());
    closeModalRef.current?.();
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
            <Loader className={`${s.loader} ${loading ? s.active : ""}`} />
          </div>
          <div className={s.search_wrapper}>
            <Search
              inputRef={inputRef}
              id={SEARCH_KEY}
              placeholder={"search.searchPlaceholder"}
            />
          </div>
          <div className={s.filters_wrapper}>
            <div className={s.search_filters}>
              <p className={s.filters_label}>
                <Trans i18nKey={"search.categories"} />
              </p>
              <CategoriesFilter
                resultKeys={RESULT_KEYS}
                loading={loading}
                searchResults={searchResults}
                selectedCategories={selectedCategories}
                urlKey={TYPES_URL_KEY}
                isBtnDisabled={!hasResults}
              />
            </div>
            <div className={s.search_filters}>
              <p className={s.filters_label}>
                <Trans i18nKey={"search.languages"} />
              </p>
              <LanguagesFilter
                selectedLanguages={selectedLanguages}
                urlKey={LANGS_URL_KEY}
                loading={loading}
              />
            </div>
          </div>

          <div className={s.results_container}>
            {showSkeleton && <ResultsListSkeleton types={selectedCategories} />}
            {showNoResults && <NoResults />}
            {hasResults && !loading && (
              <div className={s.results_list}>
                {RESULT_KEYS.map((key) => {
                  const data = searchResults[key];
                  const quantity = searchResults.counts[key];
                  if (!data || data.length === 0) return null;
                  return (
                    <ResultsList
                      key={key}
                      type={key}
                      data={data}
                      quantity={quantity}
                    />
                  );
                })}
              </div>
            )}
            {showPlaceholderCourses && (
              <div className={s.results_list}>
                <ResultsList
                  data={placeholderCourses}
                  type={"landings"}
                  quantity={placeholderCourses.length}
                  customTitle={`${t("nav.courses")} ${t("tag.common.rec")}`}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </ModalOverlay>
  );
};

export default SearchPage;
