import s from "./ProfileCourseCard.module.scss";
import ViewLink from "../../../../components/ui/ViewLink/ViewLink.tsx";
import { Link } from "react-router-dom";
import { Trans } from "react-i18next";
import Button from "../../../../components/ui/Button/Button.tsx";
import { t } from "i18next";
import { Lock } from "../../../../assets/logos/index/index.ts";

const ProfileCourseCard = ({
  isPartial = false,
  name,
  link,
  isEven,
  viewText,
  price,
  handleClick,
}: {
  isPartial?: boolean;
  viewText: string;
  name: string;
  link: string;
  isEven: boolean;
  handleClick?: () => void;
  price?: number;
}) => {
  return (
    <div
      className={`${s.card_wrapper} ${isPartial ? s.partial : ""} ${isEven ? "" : s.blue}`}
    >
      {isPartial ? (
        <>
          <div
            onClick={handleClick}
            className={`${s.card} ${isPartial ? s.blocked : ""} ${isEven ? "" : s.blue}`}
          >
            <Lock className={s.lock} />
            <h3>{name}</h3>
            <ViewLink text={viewText} />
          </div>
          <div
            onClick={handleClick}
            className={`${s.partial_card_content} ${isEven ? "" : s.blue}`}
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
        </>
      ) : (
        <Link
          to={link}
          className={`${s.card} ${isPartial ? s.blocked : ""} ${isEven ? "" : s.blue}`}
        >
          <h3>{name}</h3>
          <ViewLink text={viewText} />
        </Link>
      )}
    </div>
  );
};

export default ProfileCourseCard;
