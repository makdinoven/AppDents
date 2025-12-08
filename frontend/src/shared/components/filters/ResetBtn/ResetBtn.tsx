import s from "./ResetBtn.module.scss";
import { Trans } from "react-i18next";

const ResetBtn = ({ onClick, text }: { onClick: () => void; text: string }) => {
  return (
    <button onClick={onClick} className={s.btn}>
      <Trans i18nKey={text} />
    </button>
  );
};

export default ResetBtn;
