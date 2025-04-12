import s from "./CardsList.module.scss";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import CourseCard from "../CourseCard/CourseCard.tsx";
import { formatAuthorsDesc } from "../../../../common/helpers/helpers.ts";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";

type Course = {
  landing_name: string;
  authors: any[];
  first_tag: string;
  slug: string;
  main_image: string;
  old_price: string;
  new_price: string;
};

interface CardsListProps {
  loading: boolean;
  handleSeeMore: () => void;
  showSeeMore: boolean;
  filter?: string;
  cards: Course[] | null;
}

const CardsList: React.FC<CardsListProps> = ({
  loading,
  cards,
  filter = "all",
  showSeeMore,
  handleSeeMore,
}) => {
  const filterName = t(filter);

  return (
    <div className={s.list_wrapper}>
      {loading && (
        <div className={s.loader_overlay}>
          <Loader />
        </div>
      )}
      {cards && cards.length > 0 ? (
        <>
          <ul className={s.list}>
            {cards.map((course, index) => (
              <CourseCard
                key={index}
                index={index}
                authors={course.authors}
                old_price={course.old_price}
                new_price={course.new_price}
                name={course.landing_name}
                description={formatAuthorsDesc(course?.authors)}
                tag={course.first_tag}
                link={course.slug}
                photo={course.main_image}
              />
            ))}
          </ul>
          {showSeeMore ? (
            <PrettyButton
              text={t("seeMore")}
              variant={"primary"}
              onClick={handleSeeMore}
            />
          ) : (
            <p className={s.no_courses}>
              {filter && filter !== "all" ? (
                <Trans
                  i18nKey={t("endOfListFilter")}
                  values={{ filter: filterName }}
                />
              ) : (
                <Trans i18nKey={t("endOfList")} />
              )}
            </p>
          )}
        </>
      ) : (
        <div className={s.no_courses}>
          {filter && filter !== "all" ? (
            <Trans
              i18nKey={t("main.noCoursesFilter")}
              values={{ filter: filterName }}
            />
          ) : (
            <Trans i18nKey={"main.noCourses"} />
          )}
        </div>
      )}
    </div>
  );
};

export default CardsList;
