import s from "./CardsList.module.scss";
import CourseCard from "../CourseCard/CourseCard.tsx";
import { Trans } from "react-i18next";
import PrettyButton from "../../../ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import LoaderOverlay from "../../../ui/LoaderOverlay/LoaderOverlay.tsx";
import { Path } from "../../../../routes/routes.ts";

type Course = {
  landing_name: string;
  authors: any[];
  first_tag: string;
  slug: string;
  main_image: string;
  old_price: string;
  new_price: string;
  lessons_count: string;
};

interface CardsListProps {
  isClient?: boolean;
  loading: boolean;
  handleSeeMore?: () => void;
  showSeeMore: boolean;
  filter?: string;
  cards: Course[] | null;
  showEndOfList?: boolean;
}

const CardsList: React.FC<CardsListProps> = ({
  isClient = false,
  loading,
  cards,
  filter = "all",
  showSeeMore,
  handleSeeMore,
  showEndOfList = true,
}) => {
  const filterName = t(filter);

  return (
    <div className={s.list_wrapper}>
      {loading && <LoaderOverlay />}
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
                tag={course.first_tag}
                link={`${isClient ? `/${Path.landingClient}` : Path.landing}/${course.slug}`}
                photo={course.main_image}
                lessons_count={course.lessons_count}
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
            !loading &&
            (filter && filter !== "all" ? (
              <p className={s.no_courses}>
                <Trans
                  i18nKey={t("endOfListFilter")}
                  values={{ filter: filterName }}
                />
              </p>
            ) : (
              showEndOfList && (
                <p className={s.no_courses}>
                  <Trans i18nKey={t("endOfList")} />{" "}
                </p>
              )
            ))
          )}
        </>
      ) : (
        !loading && (
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
        )
      )}
    </div>
  );
};

export default CardsList;
