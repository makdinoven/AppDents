import s from "./SearchDropdown.module.scss";
import Search from "../../ui/Search/Search.tsx";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../../common/hooks/useOutsideClick.ts";

const mockData = [
  "apple",
  "banana",
  "orange",
  "grape",
  "pineapple",
  "mango",
  "watermelon",
];

const SearchDropdown = () => {
  const [searchValue, setSearchValue] = useState("");
  const [filteredResults, setFilteredResults] = useState<string[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  useOutsideClick(wrapperRef, () => {
    setShowDropdown(false);
  });

  useEffect(() => {
    if (searchValue.trim()) {
      const filtered = mockData.filter((item) =>
        item.toLowerCase().includes(searchValue.toLowerCase()),
      );
      setFilteredResults(filtered);
      setShowDropdown(true);
    } else {
      setFilteredResults([]);
      setShowDropdown(false);
    }
  }, [searchValue]);

  return (
    <div ref={wrapperRef} className={s.dropdown_wrapper}>
      <Search
        onFocus={() => {
          if (filteredResults.length) setShowDropdown(true);
        }}
        value={searchValue}
        placeholder={"searchCourses"}
        onChange={(e) => setSearchValue(e.target.value)}
      />
      {showDropdown && filteredResults.length > 0 && (
        <ul className={s.dropdown}>
          {filteredResults.map((item, index) => (
            <li key={index} className={s.dropdown_item}>
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchDropdown;
