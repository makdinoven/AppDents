import s from "./CoursesSection.module.scss";
import SectionHeader from "../../ui/SectionHeader/SectionHeader.tsx";
import SelectableList from "../SelectableList/SelectableList.tsx";
import CardsList from "./CardsList/CardsList.tsx";
import {
  LANGUAGES,
  SORT_FILTERS,
} from "../../../common/helpers/commonConstants.ts";
import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import {
  getCourses,
  getCoursesRecommend,
} from "../../../store/actions/mainActions.ts";
import CourseCardSkeletons from "../../ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";
import FiltersSkeleton from "../../ui/Skeletons/FiltersSkeleton/FiltersSkeleton.tsx";

type props = {
  sectionTitle?: string;
  pageSize: number;
  isClient?: boolean;
  tags?: any[];
  activeFilter?: string;
  activeSort?: string;
  showFilters?: boolean;
  showSort?: boolean;
  handleSetActiveFilter?: any;
  handleSetActiveSort?: any;
  ref?: React.RefObject<any>;
  isOffer?: boolean;
  isFree?: boolean;
  isVideo?: boolean;
};

const CoursesSection = ({
  ref,
  sectionTitle,
  pageSize,
  isClient = true,
  isVideo = false,
  isFree = false,
  tags,
  showFilters = false,
  showSort = false,
  activeFilter: externalFilter,
  activeSort: externalSort,
  handleSetActiveFilter,
  handleSetActiveSort,
  isOffer = false,
}: props) => {
  const dispatch = useDispatch<AppDispatchType>();
  const cards = useSelector((state: AppRootStateType) => state.main.courses);
  const total = useSelector(
    (state: AppRootStateType) => state.main.totalCourses,
  );
  const userLoading = useSelector(
    (state: AppRootStateType) => state.user.loading,
  );
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const loading = useSelector((state: AppRootStateType) => state.main.loading);
  const [skip, setSkip] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [internalFilter, setInternalFilter] = useState("all");
  const [internalSort, setInternalSort] = useState<string>("");
  const [isReady, setIsReady] = useState(false);
  const filter = externalFilter ?? internalFilter;
  const sort = externalSort ?? internalSort;
  const skipResetInProgress = useRef(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isFilterChangeLoading, setIsFilterChangeLoading] = useState(false);

  useEffect(() => {
    if (LANGUAGES.some((lang) => lang.value === language)) {
      setIsReady(true);
    }
  }, [language, filter, sort]);

  useEffect(() => {
    setInternalSort(isLogged ? "recommend" : "popular");
  }, [isLogged]);

  const activeFilter = externalFilter ?? internalFilter;
  const activeSort = externalSort ?? internalSort;

  useEffect(() => {
    if (skip !== 0) {
      skipResetInProgress.current = true;
      setSkip(0);
    }
  }, [language, activeFilter, activeSort]);

  useEffect(() => {
    if (activeFilter || activeSort) {
      setIsFilterChangeLoading(true);
    }
  }, [activeFilter, activeSort, language]);

  useEffect(() => {
    if (!loading) {
      setIsFilterChangeLoading(false);
      setIsLoadingMore(false);
    }
  }, [loading]);

  useEffect(() => {
    if (isReady && !userLoading) {
      if (skipResetInProgress.current) {
        skipResetInProgress.current = false;
        return;
      }

      const params = {
        language,
        limit: pageSize,
        skip,
        ...(filter !== "all" && filter !== "" && { tags: filter }),
        ...(sort !== "" && { sort }),
      };

      if (isLogged) {
        dispatch(getCoursesRecommend(params));
      } else {
        dispatch(getCourses(params));
      }
    }
  }, [isReady, language, skip, filter, sort, userLoading, isLogged]);

  const handleSeeMore = () => {
    setSkip((prev) => prev + pageSize);
    setIsLoadingMore(true);
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
        {sectionTitle && <SectionHeader name={sectionTitle} />}
        {showFilters && (
          <>
            {tags && tags.length > 0 ? (
              <>
                <SelectableList
                  items={tags}
                  activeValue={activeFilter}
                  onSelect={onFilterChange}
                />
              </>
            ) : (
              <FiltersSkeleton />
            )}
            <span className={s.line}></span>
          </>
        )}

        {showSort && (
          <div className={s.filters_wrapper}>
            <SelectableList
              items={
                isLogged
                  ? SORT_FILTERS
                  : SORT_FILTERS.filter((item) => item.value !== "recommend")
              }
              activeValue={activeSort}
              onSelect={onSortChange}
            />
          </div>
        )}
      </div>
      {!(cards.length > 0) && !!total ? (
        <CourseCardSkeletons shape />
      ) : (
        <>
          <CardsList
            showLoaderOverlay={isFilterChangeLoading}
            isVideo={isVideo}
            isFree={isFree}
            isOffer={isOffer}
            isClient={isClient}
            filter={activeFilter}
            handleSeeMore={handleSeeMore}
            loading={loading}
            cards={cards}
            showSeeMore={!loading && cards.length !== total}
          />
        </>
      )}
      {isLoadingMore && loading && (
        <CourseCardSkeletons amount={pageSize} fade moveUp shape />
      )}
    </section>
  );
};
export default CoursesSection;
