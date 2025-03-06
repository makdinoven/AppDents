import s from "./BackButton.module.scss";
import UnstyledButton from "../../CommonComponents/UnstyledButton.tsx";
import { useNavigate } from "react-router-dom";
import { Trans } from "react-i18next";
import BackArrow from "../../../common/Icons/BackArrow.tsx";

const BackButton = () => {
  const navigate = useNavigate();

  return (
    <UnstyledButton className={s.back_btn} onClick={() => navigate(-1)}>
      <BackArrow />
      {<Trans i18nKey="back" />}
    </UnstyledButton>
  );
};

export default BackButton;
