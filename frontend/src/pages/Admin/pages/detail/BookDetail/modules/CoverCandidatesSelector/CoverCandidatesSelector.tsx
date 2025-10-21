import ModalWrapper from "../../../../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import s from "./CoverCandidatesSelector.module.scss";
import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../assets/icons";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";
import { useState } from "react";
import { CoverCandidate } from "../../BookDetail.tsx";

const Component = ({
  coverCandidates,
  setCoverCandidates,
  book,
  setBook,
}: {
  coverCandidates: CoverCandidate[];
  setCoverCandidates: (c: CoverCandidate[]) => void;
  book: any;
  setBook: (data: any) => void;
}) => {
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

  return (
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
  );
};

export default Component;
