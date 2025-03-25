import s from "./CourseCard.module.scss";
import ViewLink from "../../../../components/ui/ViewLink/ViewLink.tsx";
import { useNavigate } from "react-router-dom";

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
  const navigate = useNavigate();
  const isExternal = link.startsWith("http");

  const handleClick = () => {
    if (isExternal) {
      window.open(link, "_blank", "noopener,noreferrer");
    } else {
      navigate(link);
    }
  };

  return (
    <li onClick={handleClick} className={`${s.card} ${isEven ? "" : s.blue}`}>
      <h3>{name}</h3>
      <ViewLink isExternal={isExternal} link={link} text={viewText} />
    </li>
  );
};

export default CourseCard;
