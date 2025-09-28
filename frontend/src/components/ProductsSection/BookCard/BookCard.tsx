import s from "./BookCard.module.scss";
import { BookCardType } from "../CardsList/CardsList.tsx";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";

const BookCard = ({ book }: { book: BookCardType }) => {
  const {
    language,
    landing_name,
    slug,
    old_price,
    new_price,
    publication_date,
    authors,
    index,
    images,
  } = book;
  const screenWidth = useScreenWidth();

  const setCardColor = (whatIsReturned: "className" | "color") => {
    const returnValue = whatIsReturned === "className" ? s.blue : "blue";

    if (screenWidth < 577) {
      return index % 2 === 0 ? returnValue : "";
    } else {
      return index % 4 === 0 || index % 4 === 3 ? "" : returnValue;
    }
  };

  const renderImages = Array.from({ length: 5 }).map((_, i) => {
    const image = images[i];
    const zIndex = 5 - i;
    const opacity = 1 - i * 0.1;

    return image ? (
      <div key={i} style={{ zIndex, opacity }} className={s.img_wrapper}>
        <img src={image} alt={`${i + 1}-image`} />
      </div>
    ) : (
      <div
        key={i}
        style={{ zIndex, opacity }}
        className={`${s.img_wrapper} ${s.no_photo}`}
      />
    );
  });

  return (
    <div className={s.card}>
      <div className={s.images_wrapper}>
        {/*<LangLogo />*/}
        {renderImages}
      </div>
      {/*{landing_name}*/}
      {/*<AuthorsDesc authors={authors} color={setCardColor("color")} />*/}
    </div>
  );
};

export default BookCard;
