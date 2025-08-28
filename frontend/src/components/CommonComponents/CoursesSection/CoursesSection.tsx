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

const ScreenResolutions = {
  desktop: 1440,
  tablet: 768,
  mobile: 567,
} as const;

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
    (state: AppRootStateType) => state.main.totalCourses
  );
  const userLoading = useSelector(
    (state: AppRootStateType) => state.user.loading
  );
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged
  );
  const loading = useSelector((state: AppRootStateType) => state.main.loading);
  const [skip, setSkip] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language
  );
  const [internalFilter, setInternalFilter] = useState("all");
  const [internalSort, setInternalSort] = useState<string>("");
  const [screenWidth, setScreenWidth] = useState<number>(window.innerWidth);
  const [isReady, setIsReady] = useState(false);
  const filter = externalFilter ?? internalFilter;
  const sort = externalSort ?? internalSort;
  const skipResetInProgress = useRef(false);

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

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [screenWidth]);

  const countButtonSkeletonsAmount = () => {
    if (screenWidth <= ScreenResolutions.desktop) {
      return 15;
    } else if (screenWidth <= ScreenResolutions.tablet) {
      return 12;
    } else if (screenWidth <= ScreenResolutions.mobile) {
      return 6;
    }
  };

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
        {sectionTitle && <SectionHeader name={sectionTitle} />}
        {loading ? (
          <ul className={s.skeletons}>
            {Array(countButtonSkeletonsAmount())
              .fill({ length: countButtonSkeletonsAmount() })
              .map((_, index) => (
                <li key={index} className={s.skeleton}></li>
              ))}
          </ul>
        ) : (
          showFilters &&
          tags &&
          tags.length > 0 && (
            <SelectableList
              items={tags}
              activeValue={activeFilter}
              onSelect={onFilterChange}
            />
          )
        )}
        <span className={s.line}></span>
        {loading ? (
          <ul className={s.skeletons}>
            {Array(3)
              .fill({ length: 3 })
              .map((_, index) => (
                <li key={index} className={s.skeleton}></li>
              ))}
          </ul>
        ) : (
          showSort &&
          cards.length > 0 && (
            <SelectableList
              items={
                isLogged
                  ? SORT_FILTERS
                  : SORT_FILTERS.filter((item) => item.value !== "recommend")
              }
              activeValue={activeSort}
              onSelect={onSortChange}
            />
          )
        )}
      </div>
      {loading ? (
        <CourseCardSkeletons shape />
      ) : (
        <CardsList
          isVideo={isVideo}
          isFree={isFree}
          isOffer={isOffer}
          isClient={isClient}
          filter={activeFilter}
          handleSeeMore={handleSeeMore}
          loading={loading}
          cards={cards}
          showSeeMore={cards.length !== total}
        />
      )}
    </section>
  );
};
export default CoursesSection;
