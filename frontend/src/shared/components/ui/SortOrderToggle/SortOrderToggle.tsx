import s from "./SortOrderToggle.module.scss";
import { BackArrow } from "../../../assets/icons";
import { Trans } from "react-i18next";

export type SortDirectionType = "asc" | "desc" | null;

const SortOrderToggle = ({
  sortOrder,
  setSortOrder,
  transKey,
}: {
  transKey?: string;
  sortOrder: SortDirectionType;
  setSortOrder: (direction: SortDirectionType) => void;
}) => {
  const handleSortDirectionChange = (direction: SortDirectionType) => {
    if (direction === sortOrder) {
      setSortOrder(null);
    } else {
      setSortOrder(direction);
    }
  };

  return (
    <div className={`${s.sort_container} ${!transKey ? s.center : ""}`}>
      {transKey && (
        <span>
          <Trans i18nKey={transKey} />
        </span>
      )}
      <div className={s.buttons}>
        <button
          onClick={() => handleSortDirectionChange("asc")}
          className={`${s.up_btn} ${sortOrder === "asc" ? s.active : ""}`}
        >
          <BackArrow />
        </button>
        <button
          onClick={() => handleSortDirectionChange("desc")}
          className={`${s.down_btn} ${sortOrder === "desc" ? s.active : ""}`}
        >
          <BackArrow />
        </button>
      </div>
    </div>
  );
};

export default SortOrderToggle;
