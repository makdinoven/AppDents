import s from "./CoursesSection.module.scss";
import { useEffect, useState } from "react";
import SectionHeader from "../../../components/ui/SectionHeader/SectionHeader.tsx";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import { useSearchParams } from "react-router-dom";
import CardsList from "./CardsList/CardsList.tsx";
import {
  SORT_FILTERS,
  LANGUAGES,
} from "../../../common/helpers/commonConstants.ts";
import { getTags } from "../../../store/actions/mainActions.ts";
const PAGE_SIZE = 10;

const CoursesSection = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const tags = useSelector((state: any) => state.main.tags);
  const [searchParams, setSearchParams] = useSearchParams();
  const filterFromUrl = searchParams.get("filters") || "all";
  const sortFromUrl = searchParams.get("sort") || "popular";
  const [cards, setCards] = useState<any>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string>("");
  const [activeSort, setActiveSort] = useState<string>("");
  const [skip, setSkip] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );

  useEffect(() => {
    handleSetActiveFilter(filterFromUrl);
    handleSetActiveSort(sortFromUrl);
    if (tags.length < 1) {
      dispatch(getTags());
    }
  }, []);

  useEffect(() => {
    setSkip(0);
    setCards([]);
  }, [language]);

  useEffect(() => {
    if (LANGUAGES.some((lang) => lang.value === language)) {
      fetchCourseCards();
    }
  }, [language, activeSort, activeFilter, skip]);

  const fetchCourseCards = async () => {
    setLoading(true);
    try {
      const params: any = {
        language: language,
        sort: activeSort,
        limit: PAGE_SIZE,
        ...(skip !== 0 && { skip }),
        ...(activeFilter !== "all" && { tags: activeFilter }),
      };

      const res = await mainApi.getCourseCards(params);
      if (skip === 0) {
        setCards(res.data.cards);
      } else {
        setCards((prevCards: any) => [...prevCards, ...res.data.cards]);
      }
      setTotal(res.data.total);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching courses", error);
    }
  };

  const handleSetActiveFilter = (filter: string) => {
    setActiveFilter(filter);
    if (skip !== 0) {
      setSkip(0);
    }
    const newParams = new URLSearchParams(searchParams);
    newParams.set("filters", filter);
    setSearchParams(newParams);
  };

  const handleSetActiveSort = (sort: string) => {
    setActiveSort(sort);
    if (skip !== 0) {
      setSkip(0);
    }
    const newParams = new URLSearchParams(searchParams);
    newParams.set("sort", sort);
    setSearchParams(newParams);
  };

  const handleSeeMore = () => {
    setSkip((prevSkip) => prevSkip + PAGE_SIZE);
  };

  return (
    <section className={s.courses}>
      <div className={s.courses_header}>
        <SectionHeader name={"main.ourCurses"} />
        <SelectableList
          items={tags}
          activeValue={activeFilter}
          onSelect={handleSetActiveFilter}
        />
        <span className={s.line}></span>
        <SelectableList
          items={SORT_FILTERS}
          activeValue={activeSort}
          onSelect={handleSetActiveSort}
        />
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
