import s from "./SortOrderToggle.module.scss";
import { BackArrow } from "../../../assets/icons";
import { Trans } from "react-i18next";

const SortOrderToggle = ({
  activeBtn,
  handleBtnClick,
  transKey,
}: {
  transKey: string;
  activeBtn: "asc" | "desc" | null;
  handleBtnClick: (val: "asc" | "desc") => void;
}) => {
  return (
    <div className={s.sort_container}>
      <span>
        <Trans i18nKey={transKey} />
      </span>
      <div className={s.buttons}>
        <button
          onClick={() => handleBtnClick("asc")}
          className={`${s.up_btn} ${activeBtn === "asc" ? s.active : ""}`}
        >
          <BackArrow />
        </button>
        <button
          onClick={() => handleBtnClick("desc")}
          className={`${s.down_btn} ${activeBtn === "desc" ? s.active : ""}`}
        >
          <BackArrow />
        </button>
      </div>
    </div>
  );
};

export default SortOrderToggle;
