import s from "./CourseCard.module.scss";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import Arrow from "../../../../common/Icons/Arrow.tsx";

interface CourseCardProps {
  name: string;
  description: string;
  tag: string;
  link: string;
  photo: string;
  index: number;
}

const CourseCard = ({
  name,
  description,
  tag,
  link,
  photo,
  index,
}: CourseCardProps) => {
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setScreenWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const setCardColor = () => {
    if (screenWidth < 721) {
      return index % 2 === 0 ? s.blue : "";
    } else {
      return index % 4 === 0 || index % 4 === 3 ? "" : s.blue;
    }
  };

  return (
    <li className={`${s.card} ${setCardColor()}`}>
      <div className={s.card_header}>{tag}</div>
      <div className={s.card_body}>
        <h4>{name}</h4>
        <p> {description}</p>
        <Link to={link}>
          <Trans i18nKey={"viewCourse"} />
          <Arrow />
        </Link>
        <div className={s.card_bottom}>
          <div
            style={{ backgroundImage: `url(${photo})` }}
            className={s.photo}
          ></div>
        </div>
      </div>
    </li>
  );
};

export default CourseCard;
