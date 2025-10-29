import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useState } from "react";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../../../../../assets/icons";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";

const BookMetadataSelector = ({
  book,
  setBook,
}: {
  book: any;
  setBook: (book: any) => void;
}) => {
  const [loading, setLoading] = useState(false);

  const handleCreateBookMetadata = async () => {
    if (!book.id) return;
    setLoading(true);
    try {
      const res = await adminApi.createBookMetadata(book.id, book.language);
      console.log(res.data);
      // setBook(res.data);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      Alert(`Error extracting book metadata: ${error}`, <ErrorIcon />);
    }
  };

  return (
    <PrettyButton
      variant={"primary"}
      loading={loading}
      text={"Create book metadata"}
      onClick={handleCreateBookMetadata}
    />
  );
};

export default BookMetadataSelector;
