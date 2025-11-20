import s from "./MainPage.module.scss";
import Hero from "./Hero/Hero.tsx";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";
import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import { useSearchParams } from "react-router-dom";
import { getTags } from "../../store/actions/mainActions.ts";
import { scrollToElement } from "../../common/helpers/helpers.ts";
import CustomOrder from "../../components/CommonComponents/CustomOrder/CustomOrder.tsx";
// import Feedback from "../../components/CommonComponents/Feedback/Feedback.tsx";

const PAGE_SIZE = 14;

const MainPage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const isLogged = useSelector((state: any) => state.user.isLogged);
  const tags = useSelector((state: any) => state.main.tags);
  const [searchParams, setSearchParams] = useSearchParams();
  const filterFromUrl = searchParams.get("filter");
  const sortFromUrl = searchParams.get("sort");
  const [activeFilter, setActiveFilter] = useState<string>(
    filterFromUrl ? filterFromUrl : "all",
  );
  const [activeSort, setActiveSort] = useState<string>(
    sortFromUrl ? sortFromUrl : "",
  );
  const [skip, setSkip] = useState(0);
  const coursesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!sortFromUrl) {
      setActiveSort(isLogged ? "recommend" : "popular");
    }
  }, [isLogged]);

  useEffect(() => {
    if (tags.length < 1) dispatch(getTags());
  }, []);

  const handleSetActiveParam = (param: "filter" | "sort", value: string) => {
    const setter = param === "filter" ? setActiveFilter : setActiveSort;
    setter(value);

    if (skip !== 0) {
      setSkip(0);
    }

    const newParams = new URLSearchParams(searchParams);

    if (param === "filter" && value === "all") {
      newParams.delete(param);
    } else {
      newParams.set(param, value);
    }

    setSearchParams(newParams);
  };

  return (
    <div className={s.main_page}>
      <Hero onClickScroll={() => scrollToElement(coursesRef)} />
      <ProductsSection
        ref={coursesRef}
        sectionTitle={"main.ourCurses"}
        pageSize={PAGE_SIZE}
        activeFilter={activeFilter}
        activeSort={activeSort}
        tags={tags}
        showFilters={true}
        showSort={true}
        cardType={"course"}
        productCardFlags={{ isClient: true }}
        handleSetActiveFilter={(filter: string) =>
          handleSetActiveParam("filter", filter)
        }
        handleSetActiveSort={(sort: string) =>
          handleSetActiveParam("sort", sort)
        }
      />
      <CustomOrder />
      {/*<Feedback />*/}
    </div>
  );
};

export default MainPage;
