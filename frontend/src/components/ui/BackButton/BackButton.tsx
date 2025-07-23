import s from "./BackButton.module.scss";
import UnstyledButton from "../../CommonComponents/UnstyledButton";
import { Link, useNavigate } from "react-router-dom";
import { Trans } from "react-i18next";
import { BackArrow } from "../../../assets/icons";

const BackButton = ({
  link,
  showText = true,
}: {
  link?: string;
  showText?: boolean;
}) => {
  const navigate = useNavigate();

  if (link) {
    return (
      <Link to={link} className={s.back_btn}>
        <BackArrow />
        {showText && <Trans i18nKey="back" />}
      </Link>
    );
  }

  return (
    <UnstyledButton className={s.back_btn} onClick={() => navigate(-1)}>
      <BackArrow />
      {showText && <Trans i18nKey="back" />}
    </UnstyledButton>
  );
};

export default BackButton;
