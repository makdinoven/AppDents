import s from "./CourseCard.module.scss";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import ViewLink from "../../../ui/ViewLink/ViewLink.tsx";
import { Trans } from "react-i18next";
import { Path } from "../../../../routes/routes.ts";
import { Link } from "react-router-dom";
import initialPhoto from "../../../../assets/no-pictures.png";
import FormattedAuthorsDesc from "../../../../common/helpers/FormattedAuthorsDesc.tsx";

// import Book from "../../../../assets/Icons/Book.tsx";

interface CourseCardProps {
  name: string;
  tag: string;
  link: string;
  photo: string;
  index: number;
  old_price: string;
  new_price: string;
  authors: any[];
  lessons_count: string;
}

const CourseCard = ({
  name,
  tag,
  link,
  photo,
  old_price,
  new_price,
  index,
  authors,
  lessons_count,
}: CourseCardProps) => {
  const screenWidth = useScreenWidth();
  const LANDING_LINK = `${Path.landing}/${link}`;
  const visibleAuthors = authors?.slice(0, 3).filter((author) => author.photo);

  const setCardColor = () => {
    if (screenWidth < 577) {
      return index % 2 === 0 ? s.blue : "";
    } else {
      return index % 4 === 0 || index % 4 === 3 ? "" : s.blue;
    }
  };

  const renderPhoto = () => {
    return photo ? (
      <div className={s.photo}>
        <img src={photo} alt="Course image" />
      </div>
    ) : (
      <div className={s.photo}>
        <div
          style={{ backgroundImage: `url(${initialPhoto})` }}
          className={s.no_photo}
        ></div>
      </div>
    );
  };

  return (
    <li>
      <Link className={`${s.card} ${setCardColor()}`} to={LANDING_LINK}>
        <div className={s.card_header}>
          <Trans i18nKey={tag} />
        </div>
        <div className={s.card_body}>
          <div className={s.card_content_header}>
            <div className={s.prices}>
              <span className={s.new_price}>${new_price}</span>{" "}
              <span className="crossed">${old_price}</span>
            </div>
          </div>
          <h4>{name}</h4>
          <p className={s.lessons_count}>{lessons_count}</p>
          <div className={s.course_authors}>
            {visibleAuthors?.length > 0 && (
              <ul className={s.authors_photos_list}>
                {visibleAuthors?.map((author) => (
                  <li
                    key={author.id}
                    style={{ backgroundImage: `url("${author.photo}")` }}
                    className={s.author_photo}
                  ></li>
                ))}
              </ul>
            )}
            <p>
              <FormattedAuthorsDesc authors={authors} />
            </p>
          </div>
          <div className={s.link_wrapper}>
            <ViewLink text={"viewCourse"} />
          </div>
          {screenWidth > 1024 ? (
            <div className={s.card_bottom}>{renderPhoto()}</div>
          ) : (
            <>
              {renderPhoto()}
              <div className={s.card_bottom}></div>
            </>
          )}
        </div>
      </Link>
    </li>
  );
};

export default CourseCard;
