import s from "./BookMetadataSelector.module.scss";
import ModalWrapper from "../../../../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useState } from "react";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../assets/icons";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";

type BookMetadata = {
  date_candidates: { value: number; source: string; confidence: string }[];
  page_count: number;
  publisher_candidates: { value: string; source: string; confidence: string }[];
} | null;

type SelectedPublicationYear = {
  value: number;
  source: string;
} | null;

type SelectedPublisher = {
  value: string;
  source: string;
} | null;

const BookMetadataSelector = ({
  book,
  setBook,
}: {
  book: any;
  setBook: (book: any) => void;
}) => {
  const [applyLoading, setApplyLoading] = useState(false);
  const [extractLoading, setExtractLoading] = useState(false);
  const [bookMetadata, setBookMetadata] = useState<BookMetadata>(null);
  const [selectedPublicationYear, setSelectedPublicationYear] =
    useState<SelectedPublicationYear>(null);
  const [selectedPublisher, setSelectedPublisher] =
    useState<SelectedPublisher>(null);
  const isModalOpened = !!bookMetadata;
  const usePublisherCandidates =
    !!bookMetadata && bookMetadata.date_candidates.length > 0;
  const useDateCandidates =
    !!bookMetadata && bookMetadata.date_candidates.length > 0;

  const handleApplyMetadata = async () => {
    if (!bookMetadata) {
      Alert(`No book metadata`, <ErrorIcon />);
      return;
    }
    if (!selectedPublicationYear && !selectedPublisher) {
      Alert(`Select metadata to apply`, <ErrorIcon />);
      return;
    }
    if (!selectedPublisher && usePublisherCandidates) {
      Alert(`Select publisher name to apply`, <ErrorIcon />);
      return;
    }
    if (!selectedPublicationYear && useDateCandidates) {
      Alert(`Select publication name name to apply`, <ErrorIcon />);
      return;
    }

    try {
      setApplyLoading(true);
      const res = await adminApi.applyBookMetadata(book.id, {
        page_count: bookMetadata.page_count,
        publisher_name: selectedPublisher?.value,
        publication_year: selectedPublicationYear?.value,
      });
      setBook({
        ...book,
        page_count: bookMetadata!.page_count,
        ...(useDateCandidates && {
          publication_date: selectedPublicationYear?.value,
        }),
        publishers: [res.data.publishers],
      });
      Alert(`Book metadata applied`, <CheckMark />);
      setBookMetadata(null);
      setApplyLoading(false);
    } catch (e) {
      setApplyLoading(false);
      Alert(`Error applying book metadata: ${e}`, <ErrorIcon />);
    }
  };

  const handleGetBookMetadata = async () => {
    if (!book.id) return;
    setExtractLoading(true);
    try {
      const res = await adminApi.extractBookMetadata(book.id);
      setBookMetadata(res.data);
      setExtractLoading(false);
    } catch (error) {
      setExtractLoading(false);
      Alert(`Error extracting book metadata: ${error}`, <ErrorIcon />);
    }
  };

  const renderSelector = <T extends string | number>({
    title,
    candidates,
    selected,
    onSelect,
  }: {
    title: string;
    candidates: { value: T; source: string; confidence: string }[];
    selected: { value: T; source: string } | null;
    onSelect: (candidate: { value: T; source: string }) => void;
  }) => {
    if (!candidates.length) return null;

    return (
      <div className={s.selector_container}>
        <h4>{title}</h4>
        <div className={s.buttons}>
          {candidates.map((item, i) => (
            <button
              key={i}
              className={
                selected?.value === item.value &&
                selected?.source === item.source
                  ? s.active
                  : ""
              }
              onClick={() =>
                onSelect({ value: item.value, source: item.source })
              }
            >
              {item.value}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div>
      <PrettyButton
        loading={extractLoading}
        variant={"primary"}
        text={"Get book metadata"}
        onClick={handleGetBookMetadata}
      />

      {isModalOpened && (
        <ModalWrapper
          title={"Select book metadata"}
          cutoutPosition={"none"}
          isOpen={isModalOpened}
          onClose={() => setBookMetadata(null)}
        >
          <div className={s.book_metadata_modal}>
            {renderSelector({
              title: "Select publication year",
              candidates: bookMetadata!.date_candidates,
              selected: selectedPublicationYear,
              onSelect: setSelectedPublicationYear,
            })}

            {renderSelector({
              title: "Select publisher",
              candidates: bookMetadata!.publisher_candidates,
              selected: selectedPublisher,
              onSelect: setSelectedPublisher,
            })}

            <PrettyButton
              loading={applyLoading}
              text={"Apply"}
              onClick={handleApplyMetadata}
            />
          </div>
        </ModalWrapper>
      )}
    </div>
  );
};

export default BookMetadataSelector;
