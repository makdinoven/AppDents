import s from "./CourseCard.module.scss";
import ViewLink from "../../../../components/ui/ViewLink/ViewLink.tsx";
import { Link } from "react-router-dom";

const CourseCard = ({
  name,
  link,
  isEven,
  viewText,
}: {
  viewText: string;
  name: string;
  link: string;
  isEven: boolean;
}) => {
  return (
    <Link to={link} className={`${s.card} ${isEven ? "" : s.blue}`}>
      <h3>{name}</h3>
      <ViewLink text={viewText} />
    </Link>
  );
};

export default CourseCard;
