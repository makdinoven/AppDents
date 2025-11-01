import ModalWrapper from "../../../../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import s from "./CoverCandidatesSelector.module.scss";
import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../assets/icons";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";
import { useState } from "react";

type CoverCandidate = {
  id: number;
  blob: Blob;
  url: string;
  formData: FormData;
};

const Component = ({
  book,
  setBook,
}: {
  book: any;
  setBook: (data: any) => void;
}) => {
  const [loading, setLoading] = useState(false);
  const [coverCandidates, setCoverCandidates] = useState<CoverCandidate[]>([]);
  const [selectedBookCover, setSelectedBookCover] =
    useState<CoverCandidate | null>(null);

  const handleSelectBookCover = async (data: CoverCandidate) => {
    setSelectedBookCover(data);
  };

  const handleSetCover = async () => {
    if (!selectedBookCover) {
      Alert(`Please, select book cover`, <ErrorIcon />);
      return;
    }
    try {
      const res = await adminApi.uploadImageNew(selectedBookCover.formData);
      Alert(`Book cover changed`, <CheckMark />);
      setBook({ ...book, cover_url: res.data.url });
      setCoverCandidates([]);
    } catch (e) {
      Alert(`Error loading book cover image: ${e}`, <ErrorIcon />);
    }
  };

  const handleGenerateBookCoverCandidates = async () => {
    try {
      setLoading(true);
      await adminApi.generateBookCoverCandidates(book.id);
      await handleGetBookCoverCandidates();
      setLoading(false);
    } catch {
      Alert(`Error generating book cover candidates`, <ErrorIcon />);
      setLoading(false);
    }
  };

  const handleGetBookCoverCandidates = async () => {
    try {
      const fetchWithRetry = async (
        bookId: string,
        index: number,
        retries = 5,
      ): Promise<Blob> => {
        for (let attempt = 1; attempt <= retries; attempt++) {
          try {
            const res = await adminApi.getBookCoverCandidate(bookId, index);
            return res.data;
          } catch (err: any) {
            if (err?.response?.status === 404 && attempt < retries) {
              console.warn(
                `Attempt ${attempt} for candidate ${index} failed with 404, retrying...`,
              );
              await new Promise((r) => setTimeout(r, 500));
              continue;
            }
            throw err;
          }
        }
        throw new Error(
          `Failed to fetch candidate ${index} after ${retries} retries`,
        );
      };

      const requests = [1, 2, 3].map((i) => fetchWithRetry(book.id!, i));
      const blobs = await Promise.all(requests);

      const candidates = blobs.map((blob, i) => {
        const formData = new FormData();
        formData.append("file", blob);
        formData.append("entity_type", "book_cover");
        formData.append("entity_id", String(book.id));

        return {
          id: i,
          blob,
          url: URL.createObjectURL(blob),
          formData,
        };
      });

      setCoverCandidates(candidates);
    } catch (error) {
      Alert(`Error getting candidates: ${error}`, <ErrorIcon />);
    }
  };

  if (!book) return;

  return (
    <>
      <PrettyButton
        loading={loading}
        onClick={handleGenerateBookCoverCandidates}
        text={"Get cover candidates"}
      />
      {coverCandidates.length > 0 && (
        <ModalWrapper
          title={"Select book cover"}
          cutoutPosition={"none"}
          isOpen={coverCandidates.length > 0}
          onClose={() => setCoverCandidates([])}
        >
          <div className={s.candidates_modal}>
            <div className={s.images}>
              {coverCandidates.map((c, i: number) => (
                <img
                  className={`${c.id === selectedBookCover?.id ? s.active : ""}`}
                  onClick={() => handleSelectBookCover(c)}
                  key={i}
                  src={c.url}
                  alt=""
                />
              ))}
            </div>

            <PrettyButton text={"Set cover img"} onClick={handleSetCover} />
          </div>
        </ModalWrapper>
      )}
    </>
  );
};

export default Component;
