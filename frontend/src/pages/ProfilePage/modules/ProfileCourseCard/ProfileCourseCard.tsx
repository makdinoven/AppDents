import s from "./ProfileCourseCard.module.scss";
import initialPhoto from "../../../../assets/no-pictures.png";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import { Arrow } from "../../../../assets/icons/index.ts";
import CountdownTimer from "../../../../components/ui/CountdownTimer/CountdownTimer.tsx";
import { CheckMarkIcon } from "../../../../assets/icons/index.ts";
import { Clock } from "../../../../assets/icons/index.ts";
import { Dollar } from "../../../../assets/icons/index.ts";
import { Percent } from "../../../../assets/icons/index.ts";

const ProfileCourseCard = ({
  isPartial = false,
  isOffer = false,
  name,
  link,
  index,
  previewPhoto,
  expires_at,
}: {
  isPartial?: boolean;
  isOffer?: boolean;
  viewText: string;
  name: string;
  link: string;
  index: number;
  previewPhoto: string;
  expires_at?: string;
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
    <Link
      to={link}
      className={`${s.card} ${setCardColor()} ${isOffer ? s.offer : ""}`}
    >
      {isOffer && (
        <div className={s.offer_items}>
          <div className={s.timer}>
            <Clock />
            <CountdownTimer endsAt={expires_at} />
          </div>
          <div className={s.free}>
            <Trans i18nKey={"freeCourse.freePreview"} />
          </div>
        </div>
      )}
      <div className={s.card_content}>
        <div
          // style={{ backgroundImage: `url('${previewPhoto}')` }}
          className={s.card_content_bg}
        ></div>
        <h3>{name}</h3>
        {previewPhoto ? (
          <img src={previewPhoto} alt="Course image" />
        ) : (
          <img className={s.no_photo} src={initialPhoto} alt="Course image" />
        )}
      </div>
      <div className={s.card_bottom}>
        <div
          className={`${s.status} ${isPartial ? s.partial : ""} ${isOffer ? s.special : ""}`}
        >
          {isPartial && <Dollar />}
          {!isPartial && !isOffer && <CheckMarkIcon />}
          {isOffer && <Percent />}
          <Trans
            values={{ discount: 15 }}
            i18nKey={
              isPartial
                ? "freeCourse.access.partial"
                : isOffer
                  ? "freeCourse.discount"
                  : "freeCourse.access.full"
            }
          />
        </div>
        <button className={s.watch}>
          <Arrow />
        </button>
      </div>
    </Link>
  );
};

export default ProfileCourseCard;
