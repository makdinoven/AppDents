import Hero from "./Hero/Hero.tsx";
import CoursesSection from "./CoursesSection/CoursesSection.tsx";
import { useEffect, useState } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import { useSearchParams } from "react-router-dom";
import { getTags } from "../../store/actions/mainActions.ts";
// import SearchDropdown from "../../components/CommonComponents/SearchDropdown/SearchDropdown.tsx";
// import Feedback from "../../components/CommonComponents/Feedback/Feedback.tsx";

const PAGE_SIZE = 10;

const MainPage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const tags = useSelector((state: any) => state.main.tags);
  const [searchParams, setSearchParams] = useSearchParams();
  const filterFromUrl = searchParams.get("filters") || "all";
  const sortFromUrl = searchParams.get("sort") || "popular";
  const [activeFilter, setActiveFilter] = useState<string>("");
  const [activeSort, setActiveSort] = useState<string>("");
  const [skip, setSkip] = useState(0);

  useEffect(() => {
    dispatch(getMe());
    handleSetActiveParam("filters", filterFromUrl);
    handleSetActiveParam("sort", sortFromUrl);
    if (tags.length < 1) {
      dispatch(getTags());
    }
  }, []);

  const handleSetActiveParam = (param: "filters" | "sort", value: string) => {
    const setter = param === "filters" ? setActiveFilter : setActiveSort;
    setter(value);

    if (skip !== 0) {
      setSkip(0);
    }

    const newParams = new URLSearchParams(searchParams);
    newParams.set(param, value);
    setSearchParams(newParams);
  };

  return (
    <>
      {/*<SearchDropdown />*/}
      <Hero />
      <CoursesSection
        sectionTitle={"main.ourCurses"}
        pageSize={PAGE_SIZE}
        activeFilter={activeFilter}
        activeSort={activeSort}
        tags={tags}
        showFilters={true}
        showSort={true}
        handleSetActiveFilter={(filter: string) =>
          handleSetActiveParam("filters", filter)
        }
        handleSetActiveSort={(sort: string) =>
          handleSetActiveParam("sort", sort)
        }
      />
      {/*<Feedback />*/}
    </>
  );
};

export default MainPage;
