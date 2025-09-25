import s from "./BookCard.module.scss";

const BookCard = ({ book }: { book: any }) => {
  console.log(book);
  return <div className={s.card}>book card</div>;
};

export default BookCard;
