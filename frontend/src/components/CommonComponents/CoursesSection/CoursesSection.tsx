import s from "./CoursesSection.module.scss";
import SectionHeader from "../../ui/SectionHeader/SectionHeader.tsx";
import SelectableList from "../SelectableList/SelectableList.tsx";
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
  ref?: React.RefObject<any>;
};

const CoursesSection = ({
  ref,
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
  const [isReady, setIsReady] = useState(false);
  const filter = externalFilter ?? internalFilter;
  const sort = externalSort ?? internalSort;

  useEffect(() => {
    if (LANGUAGES.some((lang) => lang.value === language)) {
      setIsReady(true);
    }
  }, [language, filter, sort]);

  const activeFilter = externalFilter ?? internalFilter;
  const activeSort = externalSort ?? internalSort;

  useEffect(() => {
    setSkip(0);
  }, [language, activeFilter, activeSort]);

  useEffect(() => {
    if (isReady) {
      const params = {
        language,
        limit: pageSize,
        skip,
        ...(filter !== "all" && filter !== "" && { tags: filter }),
        ...(sort !== "" && { sort }),
      };
      dispatch(getCourses(params));
    }
  }, [isReady, language, skip, filter, sort]);

  const handleSeeMore = () => {
    setSkip((prev) => prev + pageSize);
  };

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
    <section ref={ref} className={s.courses}>
      <div className={s.courses_header}>
        <SectionHeader name={sectionTitle} />
        {showFilters && tags && tags.length > 0 && (
          <>
            <SelectableList
              items={tags}
              activeValue={activeFilter}
              onSelect={onFilterChange}
            />
            <span className={s.line}></span>
          </>
        )}
        {showSort && cards.length > 0 && (
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
