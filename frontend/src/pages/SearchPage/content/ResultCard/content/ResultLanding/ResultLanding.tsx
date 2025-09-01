import s from "./ResultLanding.module.scss";
import LangLogo, {
  LanguagesType,
} from "../../../../../../components/ui/LangLogo/LangLogo.tsx";
import AddToCartButton from "../../../../../../components/ui/AddToCartButton/AddToCartButton.tsx";
import { formatAuthorsDesc } from "../../../../../../common/helpers/helpers.ts";
import { ResultLandingData } from "../../../../../../store/slices/mainSlice.ts";

const ResultLanding = ({
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
  data: ResultLandingData;
}) => {
  return (
    <>
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
    </>
  );
};

export default ResultLanding;
