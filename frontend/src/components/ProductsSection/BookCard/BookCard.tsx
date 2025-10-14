import s from "./BookCard.module.scss";
import { BookCardType } from "../CardsList/CardsList.tsx";
import { BOOK_FORMATS } from "../../../common/helpers/commonConstants.ts";
import { Trans } from "react-i18next";
import { Link } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import BookCardImages from "./BookCardImages/BookCardImages.tsx";
import {
  formatAuthorsDesc,
  formatLanguage,
  getPaymentType,
} from "../../../common/helpers/helpers.ts";
import { useCart } from "../../../common/hooks/useCart.ts";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";
import { CartIcon, CheckMarkIcon } from "../../../assets/icons";
import { usePaymentPageHandler } from "../../../common/hooks/usePaymentPageHandler.ts";
import { setPaymentData } from "../../../store/slices/paymentSlice.ts";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../../store/store.ts";

const BookCard = ({ book, index }: { book: BookCardType; index: number }) => {
  const { openPaymentModal } = usePaymentPageHandler();
  const dispatch = useDispatch<AppDispatchType>();
  const {
    id,
    book_ids,
    language,
    landing_name,
    slug,
    old_price,
    new_price,
    authors,
    first_tag,
    gallery,
    main_image,
  } = book;
  const { isInCart, cartItemLoading, toggleCartItem } = useCart(
    {
      id,
      landing_name,
      authors,
      page_name: slug,
      old_price,
      new_price,
      book_ids: [id],
      preview_photo: main_image,
    },
    "BOOK",
  );

  const handleAddToCart = (e: any) => {
    e.preventDefault();
    e.stopPropagation();
    toggleCartItem();
  };

  const setCardColor = () => {
    const returnValue = "blue";
    return index % 2 === 0 ? returnValue : "";
  };

  const cardColor = setCardColor();

  const link = `${Path.bookLandingClient}/${slug}`;

  const handleBuyClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    openPayment();
  };

  const openPayment = () => {
    const paymentData = {
      boookLandingIds: [id],
      bookIds: book_ids,
      priceCents: new_price * 100,
      newPrice: new_price,
      oldPrice: old_price,
      region: language,
      fromAd: false,
      itemType: "BOOK",
      books: [
        {
          name: landing_name,
          newPrice: new_price,
          oldPrice: old_price,
          img: main_image,
        },
      ],
    };

    dispatch(setPaymentData(paymentData));
    openPaymentModal(slug, getPaymentType());
  };

  return (
    <Link to={link} className={`${s.card} ${s[cardColor]}`}>
      <div className={s.card_top}>
        <div className={s.images_container}>
          <BookCardImages
            color={cardColor}
            single={gallery.length <= 1}
            images={
              gallery.length <= 1
                ? [main_image]
                : gallery.map((item: { url: string }) => item.url)
            }
          />
          <div className={s.prices}>
            <span className={s.new_price}>${new_price}</span>
            <span className={s.old_price}>${old_price}</span>
          </div>

          {first_tag && (
            <div className={s.tag}>
              <Trans i18nKey={first_tag} />
            </div>
          )}
        </div>

        <h4 lang={language.toLowerCase()} className={s.book_name}>
          {landing_name}
        </h4>

        <ul className={s.formats_list}>
          {BOOK_FORMATS.map((f) => (
            <li className={s.format_item} key={f}>
              {f}
            </li>
          ))}
        </ul>

        <ul className={s.book_info}>
          {!!authors.length && (
            <li>
              <Trans i18nKey={"bookCard.authors"} />:
              <span className={s.book_info_value}>
                {" "}
                {formatAuthorsDesc(authors)}
              </span>
            </li>
          )}
          <li>
            <Trans
              i18nKey={"bookLanding.language"}
              values={{
                language: formatLanguage(language),
              }}
              components={[<span className={s.book_info_value} />]}
            />
          </li>
        </ul>
      </div>

      <div className={s.buttons}>
        <button
          onClick={handleBuyClick}
          className={`${s.buy_btn} ${s[cardColor]}`}
        >
          {<Trans i18nKey={"buy"} />}
        </button>
        <button
          onClick={handleAddToCart}
          className={`${s.cart_btn} ${s[cardColor]} ${isInCart ? s.active : ""}`}
        >
          {isInCart ? (
            <>
              <CheckMarkIcon />
            </>
          ) : (
            <CartIcon />
          )}
          {cartItemLoading && <LoaderOverlay />}
        </button>
      </div>
    </Link>
  );
};

export default BookCard;
