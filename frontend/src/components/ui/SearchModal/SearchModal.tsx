import s from "./SearchModal.module.scss";
import Search from "../Search/Search.tsx";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../../common/hooks/useOutsideClick.ts";
import { Link, useSearchParams } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import { Trans } from "react-i18next";
import { SearchIcon } from "../../../assets/icons";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import ModalCloseButton from "../ModalCloseButton/ModalCloseButton.tsx";
import useDebounce from "../../../common/hooks/useDebounce.ts";
import { formatAuthorsDesc } from "../../../common/helpers/helpers.ts";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";
import AddToCartButton from "../AddToCartButton/AddToCartButton.tsx";

const SearchModal = ({ openKey }: { openKey: string }) => {
  const SEARCH_KEY = "global_courses_search";
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [totalResults, setTotalResults] = useState<number>(0);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language
  );
  useOutsideClick(wrapperRef, () => {
    handleDropdownClose();
  });
  const inputRef = useRef<HTMLInputElement | null>(null);
  const searchValue = searchParams.get(SEARCH_KEY);
  const debouncedSearchValue = useDebounce(searchValue, 300);

  useEffect(() => {
    if (showDropdown) {
      document.body.style.overflow = "hidden";
      inputRef.current?.focus();
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          handleDropdownClose();
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

  useEffect(() => {
    if (debouncedSearchValue) {
      handleSearch(debouncedSearchValue);
    } else {
      setSearchResults([]);
      setTotalResults(0);
    }
  }, [debouncedSearchValue]);

  const handleInputFocus = () => {
    if (searchValue?.trim()) {
      handleOpen();
    }
  };

  const handleDropdownClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      setShowDropdown(false);
      const newParams = new URLSearchParams(searchParams);
      newParams.delete(openKey);
      newParams.delete(SEARCH_KEY);
      setSearchParams(newParams, { replace: true });
    }, 150);
  };

  const handleOpen = () => {
    setShowDropdown(true);
  };

  const handleSearch = async (q: string) => {
    setLoading(true);
    try {
      const res = await mainApi.searchCourses({
        q: q.trim(),
        language,
      });
      setSearchResults(res.data.items);
      setTotalResults(res.data.total);
    } catch (error) {
      setSearchResults([]);
      console.error("Ошибка при поиске", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchParams.has(openKey)) {
      setShowDropdown(true);
    }
  }, [searchParams, openKey]);

  if (!showDropdown) return null;

  return (
    <div
      className={`${s.dropdown_wrapper} ${isClosing ? s.fadeOut : s.fadeIn}`}
    >
      <div className={s.dropdown_container}>
        <div ref={wrapperRef} className={s.dropdown_content}>
          <ModalCloseButton
            className={s.close_button}
            onClick={handleDropdownClose}
          />

          <h3 className={s.dropdown_title}>
            <Trans i18nKey={"search.searchCourses"} />
          </h3>

          <div className={s.search_wrapper}>
            <Search
              inputRef={inputRef}
              id={SEARCH_KEY}
              placeholder={"search.searchPlaceholder"}
              onFocus={handleInputFocus}
            />

            <p
              style={{ opacity: `${totalResults > 0 ? 1 : 0.7}` }}
              className={s.search_results}
            >
              <Trans i18nKey={"search.result"} count={totalResults} />
            </p>
          </div>
          {searchResults.length > 0 && (
            <ul className={s.dropdown_list}>
              {loading && <LoaderOverlay />}
              {searchResults?.map((item: any, index: number) => (
                <li key={index} onClick={() => setShowDropdown(false)}>
                  <Link
                    className={s.dropdown_item}
                    to={`${Path.landingClient}/${item.page_name}`}
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
                    <div className={s.photo_cart_wrapper}>
                      {item?.preview_photo && (
                        <div className={s.img_wrapper}>
                          <img src={item?.preview_photo} alt="" />
                        </div>
                      )}
                      <AddToCartButton
                        item={{
                          landing: {
                            id: item.id,
                            landing_name: item.landing_name,
                            authors: item.authors,
                            page_name: item.page_name,
                            old_price: item.old_price,
                            new_price: item.new_price,
                            preview_photo: item.preview_photo,
                            course_ids: item.course_ids,
                          },
                        }}
                        className={s.cart_btn}
                        variant={"primary"}
                      />
                    </div>
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

export default SearchModal;
