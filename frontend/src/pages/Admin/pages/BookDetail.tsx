import { useParams } from "react-router-dom";

const BookDetail = () => {
  const { bookId } = useParams();

  return <div>book detail page {bookId}</div>;
};

export default BookDetail;
