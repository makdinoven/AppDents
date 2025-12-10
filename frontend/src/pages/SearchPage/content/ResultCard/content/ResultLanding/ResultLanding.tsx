import s from "./ResultLanding.module.scss";
import LangLogo, {
  LanguagesType,
} from "../../../../../../shared/components/ui/LangLogo/LangLogo.tsx";
import AddToCartButton from "../../../../../../shared/components/ui/AddToCartButton/AddToCartButton.tsx";
import { formatAuthorsDesc } from "../../../../../../shared/common/helpers/helpers.ts";
import { ResultLandingData } from "../../../../../../shared/store/slices/mainSlice.ts";
import { useCart } from "../../../../../../shared/common/hooks/useCart.ts";
import { useState } from "react";
import { NoPictures } from "../../../../../../shared/assets";

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
  const [imgError, setImgError] = useState<boolean>(false);
  const { isInCart, cartItemLoading, toggleCartItem } = useCart(
    {
      id,
      landing_name,
      authors,
      page_name,
      old_price,
      new_price,
      ...(isBookLanding ? { book_ids: course_ids } : { course_ids }),
      preview_photo,
    },
    isBookLanding ? "BOOK" : "LANDING",
  );

  const handleAddToCart = () => {
    toggleCartItem();
  };

  return (
    <>
      {preview_photo && !imgError ? (
        <img
          className={`${s.photo} ${isBookLanding ? s.book : ""}`}
          src={preview_photo}
          onError={() => setImgError(true)}
          alt=""
        />
      ) : (
        <div
          className={`${s.photo} ${s.no_photo} ${isBookLanding ? s.book : ""}`}
        >
          <NoPictures />
        </div>
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
            isInCart={isInCart}
            loading={cartItemLoading}
            toggleCartItem={handleAddToCart}
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
