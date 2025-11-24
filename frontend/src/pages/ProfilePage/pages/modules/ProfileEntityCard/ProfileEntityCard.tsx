import s from "./ProfileEntityCard.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import { useScreenWidth } from "../../../../../shared/common/hooks/useScreenWidth.ts";
import { Arrow } from "../../../../../shared/assets/icons";
import CountdownTimer from "../../../../../shared/components/ui/CountdownTimer/CountdownTimer.tsx";
import { CheckMarkIcon } from "../../../../../shared/assets/icons";
import { Clock } from "../../../../../shared/assets/icons";
import { Dollar } from "../../../../../shared/assets/icons";
import { Percent } from "../../../../../shared/assets/icons";
import { NoPictures } from "../../../../../shared/assets";

const ProfileEntityCard = ({
  isPartial = false,
  isOffer = false,
  name,
  link,
  index,
  previewPhoto,
  expires_at,
  type = "course",
}: {
  isPartial?: boolean;
  isOffer?: boolean;
  viewText: string;
  name: string;
  link: string;
  index: number;
  previewPhoto: string;
  expires_at?: string;
  type?: "book" | "course";
}) => {
  const screenWidth = useScreenWidth();
  const isCourse = type === "course";

  const setCardColor = () => {
    if (screenWidth < 577) {
      return index % 2 === 0 ? "" : s.blue;
    } else if (screenWidth > 577 && screenWidth < 1025) {
      return index % 4 === 0 || index % 4 === 3 ? "" : s.blue;
    } else {
      return index % 2 === 0 ? "" : s.blue;
    }
  };

  const renderCover = () => {
    const cover = previewPhoto ? (
      <img src={previewPhoto} alt={isCourse ? "Course image" : "Book image"} />
    ) : (
      <NoPictures className={s.no_photo} />
    );

    return !isCourse ? <div className={s.cover_container}>{cover}</div> : cover;
  };

  return (
    <Link
      to={link}
      className={`${s.card} ${setCardColor()} ${isOffer ? s.offer : ""}`}
    >
      {isCourse && isOffer && (
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
      <div className={`${s.card_content} ${!isCourse ? s.book : ""}`}>
        <div
          // style={{ backgroundImage: `url('${previewPhoto}')` }}
          className={s.card_content_bg}
        ></div>
        <h3>{name}</h3>
        {renderCover()}
      </div>
      <div className={`${s.card_bottom} ${!isCourse ? s.book : ""}`}>
        {isCourse && (
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
        )}
        <button className={s.watch}>
          <Arrow />
        </button>
      </div>
    </Link>
  );
};

export default ProfileEntityCard;
