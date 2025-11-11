import ModalWrapper from "../../../../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import s from "./CoverCandidatesSelector.module.scss";
import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../assets/icons";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";

type CoverCandidate = {
  id: number;
  blob: Blob;
  url: string;
  formData: FormData;
};

const CoverCandidatesSelector = ({
  book,
  setBook,
}: {
  book: any;
  setBook: (data: any) => void;
}) => {
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [settingLoading, setSettingLoading] = useState(false);
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
      setSettingLoading(true);
      const res = await adminApi.uploadImageNew(selectedBookCover.formData);
      Alert(`Book cover changed`, <CheckMark />);
      setBook({ ...book, cover_url: res.data.url });
      setCoverCandidates([]);
      setJobStatus(null);
      setSettingLoading(false);
    } catch (e) {
      Alert(`Error loading book cover image: ${e}`, <ErrorIcon />);
    }
  };

  const handleGenerateBookCoverCandidates = async () => {
    try {
      setLoading(true);
      await adminApi.generateBookCoverCandidates(book.id);
      await handleGetCoverCandidatesJob();
    } catch {
      Alert(`Error generating book cover candidates`, <ErrorIcon />);
      setLoading(false);
    }
  };

  const handleGetCoverCandidatesJob = async () => {
    try {
      const res = await adminApi.getBookCoverCandidatesJob(book.id);
      setJobStatus(res.data.job.status);
      if (res.data.job.status === "success") {
        setLoading(false);
      }
    } catch (e) {
      Alert(
        `Error occurred while trying to get cover candidates job status`,
        <ErrorIcon />,
      );
    }
  };

  const handleGetBookCoverCandidates = async () => {
    try {
      const getCoverCandidate = async (
        bookId: string,
        index: number,
      ): Promise<Blob> => {
        const res = await adminApi.getBookCoverCandidate(bookId, index);
        return res.data;
      };

      const requests = [1, 2, 3].map((i) => getCoverCandidate(book.id!, i));
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

  useEffect(() => {
    if (!jobStatus) return;

    if (jobStatus !== "success") {
      const interval = setInterval(() => {
        handleGetCoverCandidatesJob();
      }, 3000);

      return () => clearInterval(interval);
    }

    if (jobStatus === "success") {
      handleGetBookCoverCandidates();
      setJobStatus(null);
    }
  }, [jobStatus]);

  if (!book) return;

  return (
    <>
      <PrettyButton
        loading={loading}
        onClick={handleGenerateBookCoverCandidates}
        text={"Select book cover"}
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

            <PrettyButton
              text={"Set cover img"}
              loading={settingLoading}
              onClick={handleSetCover}
            />
          </div>
        </ModalWrapper>
      )}
    </>
  );
};

export default CoverCandidatesSelector;
