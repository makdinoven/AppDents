import s from "./CourseCard.module.scss";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import ViewLink from "../../ui/ViewLink/ViewLink.tsx";
import { Trans } from "react-i18next";
import { Link } from "react-router-dom";
import AddToCartButton from "../../ui/AddToCartButton/AddToCartButton.tsx";
import AuthorsDesc from "../../ui/AuthorsDesc/AuthorsDesc.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { setPaymentData } from "../../../store/slices/paymentSlice.ts";
import { usePaymentPageHandler } from "../../../common/hooks/usePaymentPageHandler.ts";
import { getPaymentType } from "../../../common/helpers/helpers.ts";
import { useCart } from "../../../common/hooks/useCart.ts";
import { LanguagesType } from "../../ui/LangLogo/LangLogo.tsx";
import { CartItemKind } from "../../../api/cartApi/types.ts";
import { NoPictures } from "../../../assets";
import { PATHS } from "../../../../app/routes/routes.ts";
import { useState } from "react";

export type ProductCardFlags = {
  isFree?: boolean;
  isVideo?: boolean;
  isClient?: boolean;
  isOffer?: boolean;
};

interface CourseCardProps {
  id: number;
  name: string;
  tag: string;
  photo: string;
  index: number;
  old_price: number;
  new_price: number;
  authors: any[];
  lessons_count: string;
  course_ids: number[];
  slug: string;
  flags: ProductCardFlags;
}

const CourseCard = ({
  id,
  name,
  tag,
  photo,
  old_price,
  new_price,
  index,
  authors,
  lessons_count,
  course_ids,
  slug,
  flags,
}: CourseCardProps) => {
  const [imgError, setImgError] = useState<boolean>(false);
  const { openPaymentModal } = usePaymentPageHandler();
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const dispatch = useDispatch<AppDispatchType>();
  const screenWidth = useScreenWidth();
  const { isFree, isVideo, isClient, isOffer } = flags;

  const { isInCart, cartItemLoading, toggleCartItem } = useCart(
    {
      id,
      landing_name: name,
      authors,
      page_name: slug,
      old_price,
      new_price,
      course_ids: [id],
      preview_photo: photo,
    },
    "LANDING",
  );

  const link = isFree
    ? isClient
      ? PATHS.LANDING_CLIENT_FREE.build(slug)
      : PATHS.LANDING_FREE.build(slug)
    : isVideo
      ? PATHS.LANDING_VIDEO.build(slug)
      : isClient
        ? PATHS.LANDING_CLIENT.build(slug)
        : PATHS.LANDING.build(slug);

  const setCardColor = (whatIsReturned: "className" | "color") => {
    const returnValue = whatIsReturned === "className" ? s.blue : "blue";

    if (screenWidth < 577) {
      return index % 2 === 0 ? returnValue : "";
    } else {
      return index % 4 === 0 || index % 4 === 3 ? "" : returnValue;
    }
  };

  const handleBuyClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    openPayment();
  };

  const openPayment = () => {
    dispatch(
      setPaymentData({
        data: {
          new_price,
          old_price,
          course_ids,
          landing_ids: [id],
          book_ids: [],
          book_landing_ids: [],
          price_cents: new_price * 100,
          from_ad: !isClient,
          region: language as LanguagesType,
        },
        render: {
          new_price,
          old_price,
          items: [
            {
              item_type: "LANDING" as CartItemKind,
              data: {
                id,
                landing_name: name,
                authors,
                page_name: slug,
                old_price,
                new_price,
                lessons_count,
                course_ids: [id],
                preview_photo: photo,
              },
            },
          ],
        },
      }),
    );
    openPaymentModal(slug, getPaymentType(isFree, isOffer));
  };

  return (
    <>
      <li id={slug} className={`${s.card} ${setCardColor("className")}`}>
        <div className={s.card_header}>
          <Link to={link} className={s.card_header_background}>
            <Trans i18nKey={tag} />
          </Link>
        </div>
        <Link to={link} className={s.card_body}>
          <div className={s.card_content_header}>
            <div className={s.prices}>
              <span className={s.new_price}>${new_price}</span>{" "}
              <span className="crossed">${old_price}</span>
            </div>
            <p className={s.lessons_count}>{lessons_count}</p>
          </div>
          <div className={s.card_content_body}>
            <h4>{name}</h4>
            <AuthorsDesc authors={authors} color={setCardColor("color")} />
            <div className={s.content_bottom}>
              <ViewLink
                className={`${s.link_btn} ${isFree ? s.free : ""}`}
                text={"viewCourse"}
              />
              {photo && !imgError ? (
                <div className={s.photo}>
                  <img
                    src={photo}
                    alt="Course image"
                    onError={() => setImgError(true)}
                  />
                </div>
              ) : (
                <div className={`${s.photo} ${s.no_photo}`}>
                  <NoPictures />
                </div>
              )}
            </div>
            {!isFree ? (
              <div className={s.buttons}>
                <button
                  onClick={(e) => handleBuyClick(e)}
                  className={s.buy_btn}
                >
                  <Trans i18nKey={"buyNow"} />
                </button>
                {isClient && (
                  <AddToCartButton
                    toggleCartItem={toggleCartItem}
                    isInCart={isInCart}
                    loading={cartItemLoading}
                    className={s.cart_btn}
                  />
                )}
              </div>
            ) : (
              <button onClick={(e) => handleBuyClick(e)} className={s.buy_btn}>
                <Trans i18nKey={"tryCourseForFree"} />
              </button>
            )}
          </div>
        </Link>
        <Link to={link} className={s.card_bottom}></Link>
      </li>
    </>
  );
};

export default CourseCard;
