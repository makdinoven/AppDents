import s from "./CoursesSection.module.scss";
import SectionHeader from "../../../components/ui/SectionHeader/SectionHeader.tsx";
import SelectableList from "../../../components/CommonComponents/SelectableList/SelectableList.tsx";
import CardsList from "./CardsList/CardsList.tsx";
import {
  LANGUAGES,
  SORT_FILTERS,
} from "../../../common/helpers/commonConstants.ts";
import { useEffect, useState } from "react";
import { mainApi } from "../../../api/mainApi/mainApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";

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
  activeFilter = "all",
  activeSort = "popular",
  showFilters = false,
  showSort = false,
  tags,
  handleSetActiveFilter,
  handleSetActiveSort,
}: props) => {
  const [cards, setCards] = useState<any>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [skip, setSkip] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );

  useEffect(() => {
    setSkip(0);
    setCards([]);
  }, [language]);

  const handleSeeMore = () => {
    setSkip((prevSkip: number) => prevSkip + pageSize);
  };

  useEffect(() => {
    if (LANGUAGES.some((lang) => lang.value === language)) {
      fetchCourseCards();
    }
  }, [language, skip, activeFilter, activeSort]);

  const fetchCourseCards = async () => {
    setLoading(true);
    try {
      const params: any = {
        language: language,
        limit: pageSize,
        sort: activeSort,
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

  return (
    <section className={s.courses}>
      <div className={s.courses_header}>
        <SectionHeader name={sectionTitle} />
        {showFilters && tags && (
          <>
            <SelectableList
              items={tags}
              activeValue={activeFilter}
              onSelect={handleSetActiveFilter}
            />
            <span className={s.line}></span>
          </>
        )}
        {showSort && (
          <SelectableList
            items={SORT_FILTERS}
            activeValue={activeSort}
            onSelect={handleSetActiveSort}
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
