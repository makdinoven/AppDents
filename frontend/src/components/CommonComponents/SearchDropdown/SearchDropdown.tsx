import s from "./SearchDropdown.module.scss";
import Search from "../../ui/Search/Search.tsx";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../../common/hooks/useOutsideClick.ts";
import { Link } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import { Trans } from "react-i18next";
import { SearchIcon } from "../../../assets/logos/index";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import ModalCloseButton from "../../ui/ModalCloseButton/ModalCloseButton.tsx";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import { formatAuthorsDesc } from "../../../common/helpers/helpers.ts";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";

const SearchDropdown = ({
  showDropdown,
  setShowDropdown,
}: {
  showDropdown: boolean;
  setShowDropdown: (value: boolean) => void;
}) => {
  const [loading, setLoading] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [totalResults, setTotalResults] = useState<number>(0);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  useOutsideClick(wrapperRef, () => {
    handleClose();
  });
  const inputRef = useRef<HTMLInputElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (showDropdown) {
      document.body.style.overflow = "hidden";
      inputRef.current?.focus();
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          handleClose();
        }
      };
      document.addEventListener("keydown", handleKeyDown);

      return () => {
        document.body.style.overflow = "";
        document.removeEventListener("keydown", handleKeyDown);
      };
    } else {
      document.body.style.overflow = "";
    }
  }, [showDropdown]);

  const debouncedSearchValue = useDebounce(searchValue, 200);

  useEffect(() => {
    setLoading(true);
    if (debouncedSearchValue !== "") {
      handleSearch(debouncedSearchValue);
    } else {
      setSearchResults([]);
      setTotalResults(0);
    }
  }, [debouncedSearchValue]);

  const handleInputChange = (value: string) => {
    setSearchValue(value);
  };

  const handleInputFocus = () => {
    if (searchValue.trim()) {
      handleOpen();
    }
  };

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      setShowDropdown(false);
    }, 150);
  };

  const handleOpen = () => {
    setShowDropdown(true);
  };

  const handleSearch = async (query: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;
    setLoading(true);

    try {
      const res = await mainApi.searchCourses(
        query,
        language,
        controller.signal,
      );
      setSearchResults(res.data.items);
      setTotalResults(res.data.total);
    } catch (error) {
      setSearchResults([]);
      console.error("Ошибка при поиске", error);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div
      className={`${s.dropdown_wrapper} ${isClosing ? s.fadeOut : s.fadeIn}`}
    >
      <div className={s.dropdown_container}>
        <div ref={wrapperRef} className={s.dropdown_content}>
          <ModalCloseButton className={s.close_button} onClick={handleClose} />

          {totalResults === 0 && searchValue.length === 0 ? (
            <h3 className={s.dropdown_title}>
              <Trans i18nKey={"search.searchCourses"} />
            </h3>
          ) : (
            <h3
              style={{
                opacity: `${totalResults > 0 ? "1" : "0.5"}`,
              }}
              className={s.dropdown_title}
            >
              <Trans i18nKey={"search.result"} count={totalResults} />
            </h3>
          )}

          <div className={s.search_wrapper}>
            <Search
              inputRef={inputRef}
              id="searchCourses"
              value={searchValue}
              placeholder={"search.searchPlaceholder"}
              onFocus={handleInputFocus}
              onChange={(e) => handleInputChange(e.target.value)}
            />
          </div>
          {searchResults.length > 0 && (
            <ul className={s.dropdown_list}>
              {loading && <LoaderOverlay />}
              {searchResults?.map((item: any, index: number) => (
                <li key={index} onClick={handleClose}>
                  <Link
                    className={s.dropdown_item}
                    to={`${Path.landing}/${item.page_name}`}
                  >
                    <div className={s.icon}>
                      <SearchIcon />
                    </div>
                    <div className={s.dropdown_item_inner}>
                      <div className={s.prices}>
                        <span className="highlight">${item?.new_price}</span>{" "}
                        <span className="crossed">${item?.old_price}</span>
                      </div>
                      <h4>{item.landing_name}</h4>
                      <p>{formatAuthorsDesc(item?.authors)}</p>
                    </div>
                    {item?.preview_photo && (
                      <div className={s.img_wrapper}>
                        <img src={item?.preview_photo} alt="" />
                      </div>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchDropdown;
