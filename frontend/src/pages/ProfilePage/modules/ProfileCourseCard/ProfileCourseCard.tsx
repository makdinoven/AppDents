import s from "./ProfileCourseCard.module.scss";
import initialPhoto from "../../../../assets/no-pictures.png";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import Arrow from "../../../../assets/Icons/Arrow.tsx";

const ProfileCourseCard = ({
  isPartial = false,
  name,
  link,
  index,
  previewPhoto,
}: {
  isPartial?: boolean;
  viewText: string;
  name: string;
  link: string;
  index: number;
  previewPhoto?: string;
}) => {
  const screenWidth = useScreenWidth();

  const setCardColor = () => {
    if (screenWidth < 577) {
      return index % 2 === 0 ? "" : s.blue;
    } else if (screenWidth > 577 && screenWidth < 1025) {
      return index % 4 === 0 || index % 4 === 3 ? "" : s.blue;
    } else {
      return index % 2 === 0 ? "" : s.blue;
    }
  };

  return (
    <Link to={link} className={`${s.card} ${setCardColor()}`}>
      <div
        // style={{ backgroundImage: `url('${previewPhoto}')` }}
        className={s.card_content}
      >
        <h3>{name}</h3>
        {previewPhoto ? (
          <img src={previewPhoto} alt="Course image" />
        ) : (
          <img className={s.no_photo} src={initialPhoto} alt="Course image" />
        )}
      </div>
      <div className={s.card_bottom}>
        <div className={s.status}>
          <Trans
            i18nKey={
              isPartial ? "freeCourse.access.partial" : "freeCourse.access.full"
            }
          />
        </div>
        <button className={s.watch}>
          <Trans i18nKey="watch" />
          <Arrow />
        </button>
      </div>
    </Link>
  );
};

export default ProfileCourseCard;
