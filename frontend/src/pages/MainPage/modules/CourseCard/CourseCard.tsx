import s from "./CourseCard.module.scss";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import ViewLink from "../../../../components/ui/ViewLink/ViewLink.tsx";

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
  const screenWidth = useScreenWidth();

  const setCardColor = () => {
    if (screenWidth < 577) {
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
        <ViewLink link={link} text={"viewCourse"} />
        {screenWidth > 1024 ? (
          <div className={s.card_bottom}>
            <div
              style={{ backgroundImage: `url(${photo})` }}
              className={s.photo}
            ></div>
          </div>
        ) : (
          <>
            <div
              style={{ backgroundImage: `url(${photo})` }}
              className={s.photo}
            ></div>
            <div className={s.card_bottom}></div>
          </>
        )}
      </div>
    </li>
  );
};

export default CourseCard;
