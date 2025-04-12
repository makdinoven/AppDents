import s from "./CourseCard.module.scss";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import ViewLink from "../../../../components/ui/ViewLink/ViewLink.tsx";
import { Trans } from "react-i18next";
import { Path } from "../../../../routes/routes.ts";
import { Link } from "react-router-dom";

interface CourseCardProps {
  name: string;
  description: string | null;
  tag: string;
  link: string;
  photo: string;
  index: number;
  old_price: string;
  new_price: string;
  authors: any[];
}

const CourseCard = ({
  name,
  description,
  tag,
  link,
  photo,
  old_price,
  new_price,
  index,
  authors,
}: CourseCardProps) => {
  const screenWidth = useScreenWidth();
  const LANDING_LINK = `${Path.landing}/${link}`;
  const visibleAuthors = authors.slice(0, 3).filter((author) => author.photo);

  const setCardColor = () => {
    if (screenWidth < 577) {
      return index % 2 === 0 ? s.blue : "";
    } else {
      return index % 4 === 0 || index % 4 === 3 ? "" : s.blue;
    }
  };

  return (
    <li>
      <Link className={`${s.card} ${setCardColor()}`} to={LANDING_LINK}>
        <div className={s.card_header}>
          <Trans i18nKey={tag} />
        </div>
        <div className={s.card_body}>
          <div className={s.prices}>
            <span className={s.new_price}>${new_price}</span>{" "}
            <span className="crossed">${old_price}</span>
          </div>
          <h4>{name}</h4>
          <div className={s.course_authors}>
            {visibleAuthors.length > 0 && (
              <ul className={s.authors_photos_list}>
                {visibleAuthors.map((author) => (
                  <li
                    key={author.id}
                    style={{ backgroundImage: `url("${author.photo}")` }}
                    className={s.author_photo}
                  ></li>
                ))}
              </ul>
            )}
            <p> {description}</p>
          </div>
          <div className={s.link_wrapper}>
            <ViewLink text={"viewCourse"} />
          </div>
          {screenWidth > 1024 ? (
            <div className={s.card_bottom}>
              <div className={s.photo}>
                <img src={photo} alt="" />
              </div>
            </div>
          ) : (
            <>
              <div className={s.photo}>
                <img src={photo} alt="" />
              </div>
              <div className={s.card_bottom}></div>
            </>
          )}
        </div>
      </Link>
    </li>
  );
};

export default CourseCard;
