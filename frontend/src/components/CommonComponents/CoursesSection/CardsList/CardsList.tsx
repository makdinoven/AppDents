import s from "./CardsList.module.scss";
import CourseCard from "../CourseCard/CourseCard.tsx";
import { Trans } from "react-i18next";
import PrettyButton from "../../../ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import LoaderOverlay from "../../../ui/LoaderOverlay/LoaderOverlay.tsx";
import { Path } from "../../../../routes/routes.ts";
import { useLocation } from "react-router-dom";

type Course = {
  id: number;
  landing_name: string;
  authors: any[];
  first_tag: string;
  slug: string;
  main_image: string;
  old_price: number;
  new_price: number;
  lessons_count: string;
  course_ids: number[];
};

interface CardsListProps {
  isClient?: boolean;
  loading: boolean;
  handleSeeMore?: () => void;
  showSeeMore: boolean;
  filter?: string;
  cards: Course[] | null;
  showEndOfList?: boolean;
  isOffer?: boolean;
  isFree?: boolean;
  isVideo?: boolean;
}

const CardsList: React.FC<CardsListProps> = ({
  isOffer = false,
  isClient = false,
  isFree = false,
  isVideo = false,
  loading,
  cards,
  filter = "all",
  showSeeMore,
  handleSeeMore,
  showEndOfList = true,
}) => {
  const filterName = t(filter);
  const location = useLocation();
  const currentSlug = location.pathname.split("/").filter(Boolean).pop();
  const filteredCards = currentSlug
    ? cards?.filter((course) => course.slug !== currentSlug)
    : cards;

  return (
    <div className={s.list_wrapper}>
      {loading && <LoaderOverlay />}
      {filteredCards && filteredCards.length > 0 ? (
        <>
          <ul className={s.list}>
            {filteredCards.map((course, index) => (
              <CourseCard
                isFree={isFree}
                isOffer={isOffer}
                isClient={isClient}
                key={index}
                index={index}
                id={course.id}
                authors={course.authors}
                old_price={course.old_price}
                new_price={course.new_price}
                name={course.landing_name}
                tag={course.first_tag}
                slug={course.slug}
                link={
                  isFree
                    ? `/${isClient ? Path.freeLandingClient : Path.freeLanding}/${course.slug}`
                    : isVideo
                      ? `/${Path.videoLanding}/${course.slug}`
                      : `/${isClient ? Path.landingClient : Path.landing.slice(1)}/${course.slug}`
                }
                photo={course.main_image}
                lessons_count={course.lessons_count}
                course_ids={course.course_ids}
              />
            ))}
          </ul>
          {showSeeMore ? (
            <PrettyButton
              className={s.seeMoreBtn}
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
