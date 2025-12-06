import s from "./SearchPage.module.scss";
import Search from "../../shared/components/ui/Search/Search.tsx";
import { useEffect, useMemo, useRef, useState } from "react";
import useOutsideClick from "../../shared/common/hooks/useOutsideClick.ts";
import { Trans } from "react-i18next";
import ModalCloseButton from "../../shared/components/ui/ModalCloseButton/ModalCloseButton.tsx";
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
import { useListQueryParams } from "../../shared/components/list/model/useListQueryParams.ts";

const RESULT_KEYS: SearchResultKeysType[] = [
  "landings",
  "authors",
  "book_landings",
];

const LANGS_URL_KEY = "langs";
const TYPES_URL_KEY = "types";
const SEARCH_KEY = "search-q";

const toArray = <T extends string>(
  raw: string | string[] | undefined,
  fallback: T[],
): T[] => {
  if (!raw) return fallback;
  if (Array.isArray(raw)) return raw as T[];
  return [raw as T];
};

const SearchPage = () => {
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

  const closeModalRef = useRef<() => void>(null);
  const [tooLongError, setTooLongError] = useState<string | null>(null);
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

  const { params, actions } = useListQueryParams({ resetToFirstPage: false });
  const searchValue = (params[SEARCH_KEY] as string | undefined) ?? "";

  const selectedLanguages = useMemo(
    () =>
      toArray<LanguagesType>(
        params[LANGS_URL_KEY] as string | string[] | undefined,
        [language as LanguagesType],
      ),
    [params, language],
  );
  const selectedCategories = useMemo(
    () =>
      toArray<SearchResultKeysType>(
        params[TYPES_URL_KEY] as string | string[] | undefined,
        RESULT_KEYS,
      ),
    [params],
  );

  const placeholderCoursesRaw = useSelector(
    (state: AppRootStateType) => state.main.courses,
  );
  const placeholderCourses: ResultLandingData[] = placeholderCoursesRaw.map(
    mapCourseToResultLanding,
  );

  const hasResults =
    !!searchResults &&
    RESULT_KEYS.some(
      (key) => searchResults[key] && searchResults[key]!.length > 0,
    );

  const showSkeleton = loading && !!searchValue;
  const showNoResults = !hasResults && !showSkeleton && !!searchValue;
  const showPlaceholderCourses =
    !hasResults &&
    !showNoResults &&
    !!placeholderCourses.length &&
    !loading &&
    !searchValue;

  useEffect(() => {
    if (searchValue && searchValue.length > 200) {
      setTooLongError(t("search.tooLong"));
      return;
    }
    setTooLongError(null);
  }, [searchValue]);

  useEffect(() => {
    if (tooLongError) return;

    if (
      searchValue === q &&
      arraysEqual(selectedLanguagesFromStore || [], selectedLanguages) &&
      arraysEqual(selectedCategoriesFromStore || [], selectedCategories)
    ) {
      return;
    }

    if (searchValue) {
      dispatch(
        globalSearch({
          q: searchValue.trim(),
          languages: selectedLanguages,
          types: selectedCategories,
        }),
      );
    } else if (hasResults) {
      dispatch(clearSearch());
    }
  }, [
    searchValue,
    selectedLanguages,
    selectedCategories,
    tooLongError,
    q,
    hasResults,
    selectedLanguagesFromStore,
    selectedCategoriesFromStore,
    dispatch,
  ]);

  const handleClose = () => {
    dispatch(clearSearch());
    closeModalRef.current?.();
  };

  const handleLanguagesChange = (langs: LanguagesType[]) => {
    actions.set({
      [LANGS_URL_KEY]: langs.length ? langs : undefined,
    });
  };

  const handleCategoriesChange = (cats: SearchResultKeysType[]) => {
    actions.set({
      [TYPES_URL_KEY]: cats.length ? cats : undefined,
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
            <Loader className={`${s.loader} ${loading ? s.active : ""}`} />
          </div>

          <div className={s.search_wrapper}>
            <Search
              useDebounceOnChange
              error={tooLongError}
              inputRef={inputRef}
              id={SEARCH_KEY}
              placeholder={"search.searchPlaceholder"}
              valueFromUrl={searchValue}
              onChangeValue={(value) =>
                actions.set({
                  [SEARCH_KEY]: value || undefined,
                })
              }
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
                onChange={handleCategoriesChange}
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
                onChange={handleLanguagesChange}
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
