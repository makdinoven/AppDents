import s from "./ResultLanding.module.scss";
import LangLogo, {
  LanguagesType,
} from "../../../../../../components/ui/LangLogo/LangLogo.tsx";
import AddToCartButton from "../../../../../../components/ui/AddToCartButton/AddToCartButton.tsx";
import { formatAuthorsDesc } from "../../../../../../common/helpers/helpers.ts";
import { ResultLandingData } from "../../../../../../store/slices/mainSlice.ts";

const ResultLanding = ({
  type,
  data: {
    preview_photo,
    landing_name,
    new_price,
    old_price,
    language,
    id,
    authors,
    page_name,
    course_ids,
  },
}: {
  type: "book_landing" | "landing";
  data: ResultLandingData;
}) => {
  const isBookLanding = type === "book_landing";
  return (
    <>
      {preview_photo ? (
        <img
          className={`${s.photo} ${isBookLanding ? s.book : ""}`}
          src={preview_photo}
          alt=""
        />
      ) : (
        <div className={`${s.photo} ${isBookLanding ? s.book : ""}`}></div>
      )}
      <div className={s.content}>
        <div className={s.content_header}>
          <div className={s.prices}>
            {language && (
              <LangLogo
                className={s.lang_logo}
                lang={language as LanguagesType}
              />
            )}
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
        <p lang={language.toLowerCase()} className={s.name}>
          {landing_name}
        </p>
        <p lang={language.toLowerCase()} className={s.authors}>
          {formatAuthorsDesc(authors)}
        </p>
      </div>
    </>
  );
};

export default ResultLanding;
