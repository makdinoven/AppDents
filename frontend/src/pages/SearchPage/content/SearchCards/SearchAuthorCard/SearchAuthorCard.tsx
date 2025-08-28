import s from "./SearchAuthorCard.module.scss";
import LangLogo, {
  LanguagesType,
} from "../../../../../components/ui/LangLogo/LangLogo.tsx";
import { useNavigate } from "react-router-dom";
import { Path } from "../../../../../routes/routes.ts";

const SearchAuthorCard = ({
  data: { language, name, photo, id },
}: {
  data: { language: LanguagesType; name: string; photo: string; id: number };
}) => {
  const navigate = useNavigate();
  return (
    <div onClick={() => navigate(`${Path.professor}/${id}`)} className={s.card}>
      <LangLogo lang={language} />
      {name}
      {photo ? (
        <img className={s.photo} src={photo} alt="author photo" />
      ) : (
        <div className={s.photo}></div>
      )}
    </div>
  );
};

export default SearchAuthorCard;
