import s from "./CardsList.module.scss";
import CourseCard, { ProductCardFlags } from "../CourseCard/CourseCard.tsx";
import { Trans } from "react-i18next";
import PrettyButton from "../../ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";
import BookCard from "../BookCard/BookCard.tsx";
import BooksImg from "../../../assets/BOOK_IMG.png";
import { LanguagesType } from "../../ui/LangLogo/LangLogo.tsx";

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

export type BookCardType = {
  id: number;
  index: number;
  landing_name: string;
  language: LanguagesType;
  publication_date: string;
  authors: any[];
  first_tag: string;
  slug: string;
  images: string[];
  old_price: number;
  new_price: number;
  book_ids: number[];
  tags: string[];
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
      cards: BookCardType[] | null;
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
                  <BookCard
                    book={{
                      id: book.id,
                      language: "EN",
                      landing_name:
                        "Art and Nature In Ceramic Restorations Nature In Ceramiс and art",
                      slug: "///sdds",
                      old_price: 190,
                      new_price: 19,
                      publication_date: "09.02.1021",
                      index: index,
                      tags: ["surgery", "orthopedics"],
                      authors: [
                        {
                          id: 1621,
                          name: "BILL DISCHINGER",
                          photo:
                            "https://dent-s.com/assets/img/preview_img/b9f23bdcad574a8bb3d16ec31901bb3a.png",
                        },
                        {
                          id: 1622,
                          name: "ALFREDO RIZZO",
                          photo:
                            "https://dent-s.com/assets/img/preview_img/e264710492764d09b55ea792b0723ab8.png",
                        },
                        {
                          id: 1623,
                          name: "Trevor Nichols",
                          photo:
                            "https://dent-s.com/assets/img/preview_img/4cfe995dd4ae45d89b28207cd1c22015.png",
                        },
                      ],
                      book_ids: book.book_ids,
                      images: [
                        BooksImg,
                        BooksImg,
                        BooksImg,
                        // BooksImg
                      ],
                      first_tag: book.first_tag,
                    }}
                    key={book.id}
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
