import s from "./LessonCard.module.scss";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import { t } from "i18next";
import initialPhoto from "../../../../../assets/no-pictures.png";
import ViewLink from "../../../../../components/ui/ViewLink/ViewLink.tsx";
import Button from "../../../../../components/ui/Button/Button.tsx";
import { Lock } from "../../../../../assets/icons";

const LessonCard = ({
  isPartial = false,
  name,
  link,
  viewText,
  price,
  handleClick,
  index,
  previewPhoto,
}: {
  type: "course" | "lesson";
  isPartial?: boolean;
  viewText: string;
  name: string;
  link: string;
  handleClick?: () => void;
  price?: number;
  index: number;
  previewPhoto?: string;
}) => {
  const setCardColor = () => {
    return index % 2 === 0 ? "" : s.blue;
  };

  const renderLessonCard = (isBlocked: boolean) => {
    return (
      <Link
        style={{ pointerEvents: isBlocked ? "none" : "all" }}
        to={link}
        className={`${s.card} ${isBlocked ? s.blocked : ""} ${setCardColor()}`}
      >
        <div className={s.card_inner}>
          <h3>{name}</h3>
          <ViewLink text={viewText} />
        </div>
        {previewPhoto ? (
          <div className={s.photo}>
            <img src={previewPhoto} alt={""} />
          </div>
        ) : (
          <div className={s.photo}>
            <div
              style={{ backgroundImage: `url(${initialPhoto})` }}
              className={s.no_photo}
            ></div>
          </div>
        )}
      </Link>
    );
  };

  return (
    <div
      className={`${s.card_wrapper} ${isPartial ? s.partial : ""} ${setCardColor()}`}
    >
      {isPartial && (
        <div
          onClick={handleClick}
          className={` ${s.blocked_card_wrapper} ${setCardColor()}`}
        >
          <div className={s.lock_wrapper}>
            <Lock className={s.lock} />
          </div>
          <div
            onClick={handleClick}
            className={`${s.partial_card_content} ${setCardColor()}`}
          >
            <div className={s.partial_card_content_text}>
              <p className={s.upgrade_required}>
                <Trans i18nKey={"freeCourse.title"} />
              </p>
              <p className={s.part_of_course}>
                <Trans i18nKey={"freeCourse.desc"} />
              </p>
            </div>
            <Button
              variant={"outlined"}
              text={t("freeCourse.get", { count: price })}
            />
          </div>
        </div>
      )}

      {renderLessonCard(isPartial)}
    </div>
  );
};

export default LessonCard;
