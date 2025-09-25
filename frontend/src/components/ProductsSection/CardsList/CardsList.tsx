import s from "./CardsList.module.scss";
import CourseCard, { ProductCardFlags } from "../CourseCard/CourseCard.tsx";
import { Trans } from "react-i18next";
import PrettyButton from "../../ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";
import BookCard from "../BookCard/BookCard.tsx";

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

type Book = {
  id: number;
  landing_name: string;
  authors: any[];
  first_tag: string;
  slug: string;
  main_image: string;
  old_price: number;
  new_price: number;
  course_ids: number[];
};

type CardsListProps =
  | {
      loading: boolean;
      handleSeeMore?: () => void;
      showSeeMore: boolean;
      filter?: string;
      cards: Course[] | null;
      showEndOfList?: boolean;
      showLoaderOverlay?: boolean;
      productCardFlags: ProductCardFlags;
      cardType: "course";
    }
  | {
      loading: boolean;
      handleSeeMore?: () => void;
      showSeeMore: boolean;
      filter?: string;
      cards: Book[] | null;
      showEndOfList?: boolean;
      showLoaderOverlay?: boolean;
      productCardFlags: ProductCardFlags;
      cardType: "book";
    };

const CardsList: React.FC<CardsListProps> = ({
  productCardFlags,
  loading,
  showLoaderOverlay,
  cards,
  filter = "all",
  showSeeMore,
  handleSeeMore,
  showEndOfList = true,
  cardType,
}) => {
  const filterName = t(filter);

  return (
    <div className={s.list_wrapper}>
      {showLoaderOverlay && <LoaderOverlay />}
      {cards && cards.length > 0 ? (
        <>
          <ul className={`${s.list} ${cardType === "book" ? s.books : ""}`}>
            {cardType === "course"
              ? cards.map((course, index) => (
                  <CourseCard
                    flags={productCardFlags}
                    key={index}
                    index={index}
                    id={course.id}
                    authors={course.authors}
                    old_price={course.old_price}
                    new_price={course.new_price}
                    name={course.landing_name}
                    tag={course.first_tag}
                    slug={course.slug}
                    photo={course.main_image}
                    lessons_count={course.lessons_count}
                    course_ids={course.course_ids}
                  />
                ))
              : cards.map((book, index) => (
                  <BookCard book={book} key={index} />
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
                  i18nKey={t(`endOfListFilter`)}
                  values={{ filter: filterName }}
                />
              </p>
            ) : (
              showEndOfList && (
                <p className={s.no_courses}>
                  <Trans i18nKey={t(`endOfList`)} />{" "}
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
                i18nKey={t(`main.noCoursesFilter`)}
                values={{ filter: filterName }}
              />
            ) : (
              <Trans i18nKey={`main.noCourses`} />
            )}
          </div>
        )
      )}
    </div>
  );
};

export default CardsList;
