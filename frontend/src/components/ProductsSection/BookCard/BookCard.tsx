import s from "./BookCard.module.scss";
import { BookCardType } from "../CardsList/CardsList.tsx";
import { BOOK_FORMATS } from "../../../common/helpers/commonConstants.ts";
import { Trans } from "react-i18next";
import AddToCartButton from "../../ui/AddToCartButton/AddToCartButton.tsx";
import { Link } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import BookCardImages from "./BookCardImages/BookCardImages.tsx";
import {
  formatAuthorsDesc,
  formatLanguage,
} from "../../../common/helpers/helpers.ts";

const BookCard = ({ book, index }: { book: BookCardType; index: number }) => {
  const {
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

  const setCardColor = () => {
    const returnValue = "blue";
    return index % 2 === 0 ? returnValue : "";
  };

  const cardColor = setCardColor();

  const link = `${Path.bookLandingClient}/${slug}`;

  const handleBuyClick = (e: any) => {
    e.preventDefault();
    e.stopPropagation();
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
          {first_tag && (
            <li>
              <Trans i18nKey={first_tag} />
            </li>
          )}
          {!!authors.length && (
            <li>
              <Trans i18nKey={"authors"} />:
              <span className={s.book_info_value}>
                {" "}
                {formatAuthorsDesc(authors)}
              </span>
            </li>
          )}
          <li>
            <Trans i18nKey={"language"} />:
            <span className={s.book_info_value}>
              {" "}
              {formatLanguage(language)}
            </span>
          </li>
        </ul>
      </div>

      <div className={s.buttons}>
        <button
          onClick={(e) => handleBuyClick(e)}
          className={`${s.buy_btn} ${s[cardColor]}`}
        >
          {<Trans i18nKey={"buy"} />}
        </button>
        <AddToCartButton className={`${s.cart_btn} ${s[cardColor]}`} />
      </div>
    </Link>
  );
};

export default BookCard;
