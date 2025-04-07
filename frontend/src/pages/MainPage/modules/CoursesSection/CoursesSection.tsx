import s from "./CoursesSection.module.scss";
import { useEffect, useState } from "react";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../store/store.ts";
import { transformTags } from "../../../../common/helpers/helpers.ts";
import SelectableList from "../../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import { useSearchParams } from "react-router-dom";
import CardsList from "./CardsList/CardsList.tsx";
import {
  SORT_FILTERS,
  LANGUAGES,
} from "../../../../common/helpers/commonConstants.ts";
const PAGE_SIZE = 10;

const CoursesSection = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const filterFromUrl = searchParams.get("filters") || "all";
  const sortFromUrl = searchParams.get("sort") || "popular";
  const [cards, setCards] = useState<any>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [tags, setTags] = useState<any>([]);
  const [activeFilter, setActiveFilter] = useState<string>("");
  const [activeSort, setActiveSort] = useState<string>("");
  const [skip, setSkip] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );

  useEffect(() => {
    handleSetActiveFilter(filterFromUrl);
    handleSetActiveSort(sortFromUrl);
    fetchTags();
  }, []);

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
      };

      if (skip !== 0) {
        params.skip = skip;
      }

      if (activeFilter !== "all") {
        params.tags = activeFilter;
      }

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

  const fetchTags = async () => {
    try {
      const res = await mainApi.getTags();
      setTags(transformTags(res.data));
    } catch (error) {
      console.error("Error fetching tags", error);
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
