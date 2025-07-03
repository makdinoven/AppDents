import s from "./LineArrow.module.scss";
import { CircleArrow } from "../../../assets/icons";

const LineArrow = () => {
  return (
    <div className={s.line_arrow}>
      <span></span>
      <CircleArrow />
    </div>
  );
};

export default LineArrow;
