import s from "./SearchPage.module.scss";
import Search from "../../components/ui/Search/Search.tsx";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../common/hooks/useOutsideClick.ts";
import { useSearchParams } from "react-router-dom";
import { Trans } from "react-i18next";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import ModalCloseButton from "../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import useDebounce from "../../common/hooks/useDebounce.ts";
import ModalOverlay from "../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import ResultList from "./content/ResultsList/ResultsList.tsx";
import { AppRootStateType } from "../../store/store.ts";
import { useSelector } from "react-redux";
import LoaderOverlay from "../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import { t } from "i18next";
import ToggleButton from "../../components/ui/ToggleButton/ToggleButton.tsx";
import { LANGUAGES } from "../../common/helpers/commonConstants.ts";
import LangLogo, {
  LanguagesType,
} from "../../components/ui/LangLogo/LangLogo.tsx";

type SearchResults = {
  landings: any[] | null;
  authors: any[] | null;
  book_landings: any[] | null;
  counts: Record<"landings" | "authors" | "book_landings", number>;
};

const RESULT_KEYS: (keyof Omit<SearchResults, "counts">)[] = [
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
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResults | null>(
    null,
  );
  // const [totalResults, setTotalResults] = useState<number>(0);
  const closeModalRef = useRef<() => void>(null);
  const [selectedLanguages, setSelectedLanguages] = useState([language]);
  const [selectedResultTypes, setSelectedResultTypes] = useState(RESULT_KEYS);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  useOutsideClick(wrapperRef, () => {
    handleClose();
  });
  const inputRef = useRef<HTMLInputElement | null>(null);
  const searchValue = searchParams.get(SEARCH_KEY);
  const debouncedSearchValue = useDebounce(searchValue, 300);

  useEffect(() => {
    if (debouncedSearchValue) {
      handleSearch(debouncedSearchValue);
    } else {
      setSearchResults(null);
      // setTotalResults(0);
    }
  }, [debouncedSearchValue, selectedLanguages, selectedResultTypes]);

  const handleClose = () => {
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

  const handleSearch = async (q: string) => {
    setLoading(true);
    try {
      const res = await mainApi.globalSearch({
        q: q.trim(),
        languages: selectedLanguages,
        types: selectedResultTypes,
      });
      setSearchResults({
        landings: res.data.landings,
        book_landings: res.data.book_landings,
        authors: res.data.authors,
        counts: res.data.counts,
      });
      // setTotalResults(res.data.total);
    } catch (error) {
      setSearchResults(null);
      console.error("Ошибка при поиске", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalOverlay
      isVisibleCondition={true}
      isUsedAsPage
      modalPosition={"top"}
      onInitClose={(fn) => (closeModalRef.current = fn)}
    >
      <div ref={wrapperRef} className={s.modal}>
        <div className={s.modal_header}>
          <ModalCloseButton className={s.close_button} onClick={handleClose} />

          <h3 className={s.dropdown_title}>
            <Trans i18nKey={"nav.search"} />
          </h3>

          <ul className={s.languages_list}>
            {LANGUAGES.map((lang) => (
              <li key={lang.value}>
                <LangLogo
                  isChecked={selectedLanguages.includes(lang.value)}
                  isHoverable
                  className={s.lang_logo}
                  lang={lang.value as LanguagesType}
                  onClick={() => handleSelect(lang.value, setSelectedLanguages)}
                />
              </li>
            ))}
          </ul>
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
          <div className={s.search_filters}>
            {RESULT_KEYS.map((key) => (
              <ToggleButton
                key={key}
                isActive={selectedResultTypes.includes(key)}
                onClick={() => handleSelect(key, setSelectedResultTypes)}
                text={`${t(`search.results.${key}`)} ${searchResults?.counts[key] ?? 0}`}
              />
            ))}
          </div>
        </div>

        {searchResults && (
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
      </div>
    </ModalOverlay>
  );
};

export default SearchPage;
