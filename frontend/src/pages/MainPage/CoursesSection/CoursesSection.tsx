import s from "./CoursesSection.module.scss";
import SectionHeader from "../../../components/ui/SectionHeader/SectionHeader.tsx";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import CardsList from "./CardsList/CardsList.tsx";
import {
  LANGUAGES,
  SORT_FILTERS,
} from "../../../common/helpers/commonConstants.ts";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { getCourses } from "../../../store/actions/mainActions.ts";

type props = {
  sectionTitle: string;
  pageSize: number;
  tags?: any[];
  activeFilter?: string;
  activeSort?: string;
  showFilters?: boolean;
  showSort?: boolean;
  handleSetActiveFilter?: any;
  handleSetActiveSort?: any;
};

const CoursesSection = ({
  sectionTitle,
  pageSize,
  tags,
  showFilters = false,
  showSort = false,
  activeFilter: externalFilter,
  activeSort: externalSort,
  handleSetActiveFilter,
  handleSetActiveSort,
}: props) => {
  // const [cards, setCards] = useState<any>([]);
  // const [total, setTotal] = useState(0);
  // const [loading, setLoading] = useState(false);
  const dispatch = useDispatch<AppDispatchType>();
  const cards = useSelector((state: AppRootStateType) => state.main.courses);
  const total = useSelector(
    (state: AppRootStateType) => state.main.totalCourses,
  );
  const loading = useSelector((state: AppRootStateType) => state.main.loading);
  const [skip, setSkip] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [internalFilter, setInternalFilter] = useState("all");
  const [internalSort, setInternalSort] = useState("popular");

  const activeFilter = externalFilter ?? internalFilter;
  const activeSort = externalSort ?? internalSort;

  useEffect(() => {
    setSkip(0);
  }, [language]);

  useEffect(() => {
    if (LANGUAGES.some((lang) => lang.value === language)) {
      dispatch(
        getCourses({
          language,
          limit: pageSize,
          skip,
          sort: activeSort,
          filters: activeFilter,
        }),
      );
    }
  }, [language, skip, activeFilter, activeSort]);

  const handleSeeMore = () => {
    setSkip((prev) => prev + pageSize);
  };

  // useEffect(() => {
  //   if (LANGUAGES.some((lang) => lang.value === language)) {
  //     fetchCourseCards();
  //   }
  // }, [language, skip, activeFilter, activeSort]);

  // const fetchCourseCards = async () => {
  //   setLoading(true);
  //   try {
  //     const params: any = {
  //       language,
  //       limit: pageSize,
  //       ...(skip !== 0 && { skip }),
  //       ...(activeSort !== "" && { sort: activeSort }),
  //       ...(activeFilter !== "all" &&
  //         activeFilter !== "" && { filters: activeFilter }),
  //     };
  //
  //     const res = await mainApi.getCourseCards(params);
  //     if (skip === 0) {
  //       setCards(res.data.cards);
  //     } else {
  //       setCards((prev: any) => [...prev, ...res.data.cards]);
  //     }
  //     setTotal(res.data.total);
  //   } catch (error) {
  //     console.error("Error fetching courses", error);
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const onFilterChange = (val: string) => {
    if (handleSetActiveFilter) {
      handleSetActiveFilter(val);
    } else {
      setInternalFilter(val);
      setSkip(0);
    }
  };

  const onSortChange = (val: string) => {
    if (handleSetActiveSort) {
      handleSetActiveSort(val);
    } else {
      setInternalSort(val);
      setSkip(0);
    }
  };

  return (
    <section className={s.courses}>
      <div className={s.courses_header}>
        <SectionHeader name={sectionTitle} />
        {showFilters && tags && (
          <>
            <SelectableList
              items={tags}
              activeValue={activeFilter}
              onSelect={onFilterChange}
            />
            <span className={s.line}></span>
          </>
        )}
        {showSort && (
          <SelectableList
            items={SORT_FILTERS}
            activeValue={activeSort}
            onSelect={onSortChange}
          />
        )}
      </div>
      <CardsList
        filter={activeFilter}
        handleSeeMore={handleSeeMore}
        loading={loading}
        cards={cards}
        showSeeMore={cards.length !== total}
      />
    </section>
  );
};
export default CoursesSection;
