import s from "./CourseCard.module.scss";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import ViewLink from "../../ui/ViewLink/ViewLink.tsx";
import { Trans } from "react-i18next";
import { Link } from "react-router-dom";
import initialPhoto from "../../../assets/no-pictures.png";
import AddToCartButton from "../../ui/AddToCartButton/AddToCartButton.tsx";
import AuthorsDesc from "../../ui/AuthorsDesc/AuthorsDesc.tsx";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { setPaymentData } from "../../../store/slices/paymentSlice.ts";
import { usePaymentPageHandler } from "../../../common/hooks/usePaymentPageHandler.ts";
import { getPaymentType } from "../../../common/helpers/helpers.ts";
import { Path } from "../../../routes/routes.ts";
import { useCart } from "../../../common/hooks/useCart.ts";

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
    ? `/${isClient ? Path.freeLandingClient : Path.freeLanding}/${slug}`
    : isVideo
      ? `/${Path.videoLanding}/${slug}`
      : `/${isClient ? Path.landingClient : Path.landing.slice(1)}/${slug}`;

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
    const paymentData = {
      landingIds: [id],
      courseIds: course_ids,
      priceCents: new_price * 100,
      newPrice: new_price,
      oldPrice: old_price,
      region: language,
      fromAd: !isClient,
      courses: [
        {
          name: name,
          newPrice: new_price,
          oldPrice: old_price,
          lessonsCount: lessons_count,
          img: photo,
        },
      ],
    };

    dispatch(setPaymentData(paymentData));
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
              {photo ? (
                <div className={s.photo}>
                  <img src={photo} alt="Course image" />
                </div>
              ) : (
                <div className={s.photo}>
                  <div
                    style={{ backgroundImage: `url(${initialPhoto})` }}
                    className={s.no_photo}
                  ></div>
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
