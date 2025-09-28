import s from "./BookCard.module.scss";
import { BookCardType } from "../CardsList/CardsList.tsx";
import LangLogo from "../../ui/LangLogo/LangLogo.tsx";
import { BOOK_FORMATS } from "../../../common/helpers/commonConstants.ts";
import { Trans } from "react-i18next";
import AuthorsDesc from "../../ui/AuthorsDesc/AuthorsDesc.tsx";
import AddToCartButton from "../../ui/AddToCartButton/AddToCartButton.tsx";
import { Link } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import BookCardImages from "./BookCardImages/BookCardImages.tsx";

const BookCard = ({ book }: { book: BookCardType }) => {
  const {
    language,
    landing_name,
    slug,
    old_price,
    new_price,
    publication_date,
    authors,
    tags,
    index,
    images,
  } = book;
  // const screenWidth = useScreenWidth();

  const setCardColor = (whatIsReturned: "className" | "color") => {
    const returnValue = whatIsReturned === "className" ? s.blue : "blue";
    return index % 2 === 0 ? returnValue : "";
  };

  const link = `${Path.bookLandingClient}/${slug}`;

  const handleBuyClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  return (
    <Link to={link} className={`${s.card} ${setCardColor("className")}`}>
      <div className={s.card_top}>
        <div className={s.images_container}>
          <BookCardImages images={images} />
          <LangLogo
            className={s.lang_logo}
            isHoverable={false}
            lang={language}
          />
          <div className={s.prices}>
            <span className={s.new_price}>${new_price}</span>
            <span className={s.old_price}>${old_price}</span>
          </div>
        </div>

        <h4 className={s.book_name}>{landing_name}</h4>
      </div>

      <div className={s.card_bottom}>
        <ul className={s.formats_list}>
          {BOOK_FORMATS.map((f) => (
            <li className={s.format_item} key={f}>
              {f}
            </li>
          ))}
        </ul>

        <ul className={s.book_info}>
          <li>
            <Trans i18nKey={"publication.date"} />:
            <span className={s.book_info_value}> {publication_date}</span>
          </li>
          <li>
            <Trans i18nKey={"tags"} />:
            <span className={s.book_info_value}> {tags}</span>
          </li>
        </ul>

        <AuthorsDesc
          size={"small"}
          authors={authors}
          color={setCardColor("color")}
        />

        <div className={s.buttons}>
          <button
            onClick={(e) => handleBuyClick(e)}
            className={`${s.buy_btn} ${setCardColor("className")}`}
          >
            {<Trans i18nKey={"buy"} />}
          </button>
          <AddToCartButton
            className={`${s.cart_btn} ${setCardColor("className")}`}
          />
        </div>
      </div>
    </Link>
  );
};

export default BookCard;
