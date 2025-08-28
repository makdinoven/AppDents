import s from "./SearchCourseCard.module.scss";
import { Path } from "../../../../../routes/routes.ts";
import { useNavigate } from "react-router-dom";
import { formatAuthorsDesc } from "../../../../../common/helpers/helpers.ts";
import AddToCartButton from "../../../../../components/ui/AddToCartButton/AddToCartButton.tsx";
import LangLogo, {
  LanguagesType,
} from "../../../../../components/ui/LangLogo/LangLogo.tsx";

type DataType = {
  id: number;
  landing_name: string;
  new_price: number;
  old_price: number;
  preview_photo: string;
  page_name: string;
  authors: any[];
  course_ids: number[];
  language: string;
};

const SearchCourseCard = ({
  data: {
    id,
    landing_name,
    new_price,
    old_price,
    preview_photo,
    page_name,
    authors,
    course_ids,
    language,
  },
}: {
  data: DataType;
}) => {
  const navigate = useNavigate();

  const navigateToResult = () => {
    navigate(`/${Path.landingClient}/${page_name}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <li onClick={navigateToResult} className={s.card}>
      {preview_photo ? (
        <img className={s.photo} src={preview_photo} alt="" />
      ) : (
        <div className={s.photo}></div>
      )}
      <div className={s.content}>
        <div className={s.content_header}>
          <div className={s.prices}>
            <LangLogo lang={language as LanguagesType} />
            <span className={s.new_price}>${new_price}</span>
            <span className={s.old_price}>${old_price}</span>
          </div>
          <AddToCartButton
            item={{
              landing: {
                id: id,
                landing_name: landing_name,
                authors: authors,
                page_name: page_name,
                old_price: old_price,
                new_price: new_price,
                preview_photo: preview_photo,
                course_ids: course_ids,
              },
            }}
            className={s.cart_btn}
            variant={"primary"}
          />
        </div>

        <p className={s.name}>{landing_name}</p>
        <p className={s.authors}>{formatAuthorsDesc(authors)}</p>
      </div>
    </li>
  );
};

export default SearchCourseCard;
