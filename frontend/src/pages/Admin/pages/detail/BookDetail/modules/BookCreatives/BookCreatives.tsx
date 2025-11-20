import s from "./BookCreatives.module.scss";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";
import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useState } from "react";
import LoaderOverlay from "../../../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import RegenerateCreative from "./RegenerateCreative/RegenerateCreative.tsx";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../assets/icons";

export type Creative = {
  code: string;
  creative_code: string;
  status: string;
  s3_url: string;
  payload_used: { layers: any };
};

// type StatusType = "done" | "error" | "queued" | "processing";

const BookCreatives = ({ book }: { book: any }) => {
  const [loading, setLoading] = useState(false);
  const [creatives, setCreatives] = useState<null | Creative[]>(null);
  // const [status, setStatus] = useState<StatusType | null>(null);

  const handleGetOrCreateCreative = async (regen: boolean) => {
    if (regen) {
      if (
        !confirm(
          `Are you sure you want to regenerate creatives? This action will cost some money.`,
        )
      )
        return;
    }

    setLoading(true);
    try {
      const res = await adminApi.getOrCreateBookCreatives(
        book.id,
        book.language,
        regen,
      );
      if (res.data.overall === "ready") {
        setCreatives(res.data.items);
        setLoading(false);
      }

      if (res.data.task_id) {
        // setStatus(res.data.status);
        pollStatus(res.data.task_id);
      }
    } catch (error: any) {
      Alert(
        `Error creating creative: ${error.response.data.detail}`,
        <ErrorIcon />,
      );
      setLoading(false);
    }
  };

  const handleGetStatus = async (task_id: number) => {
    try {
      const res = await adminApi.getBookCreativesStatus(task_id);
      // setStatus(res.data.state);
      if (res.data.state === "error") {
        setLoading(false);
        Alert(`Error: ${res.data.error}`, <ErrorIcon />);
      }
      if (res.data.state === "done") {
        setCreatives(res.data.result.items);
        Alert("Creatives generated", <CheckMark />);
        setLoading(false);
      }
      return res.data.state;
    } catch (e) {
      console.error("Request error:", e);
      return null;
    }
  };

  const pollStatus = async (task_id: number) => {
    let isActive = true;

    while (isActive) {
      const newStatus = await handleGetStatus(task_id);

      if (newStatus === "done" || newStatus === "error") {
        isActive = false;
        break;
      }

      await new Promise((res) => setTimeout(res, 10000));
    }
  };

  return (
    <div className={s.creatives_container}>
      <div className={s.creatives_header}>
        <h4>Book creatives</h4>
        {!creatives ? (
          <PrettyButton
            loading={loading}
            text={"Get creatives"}
            onClick={() => handleGetOrCreateCreative(false)}
          />
        ) : (
          <PrettyButton
            variant={"danger"}
            loading={loading}
            text={"Regenerate all"}
            onClick={() => handleGetOrCreateCreative(true)}
          />
        )}
      </div>

      {creatives && creatives.length > 0 && (
        <div className={s.creatives_list}>
          {loading && <LoaderOverlay />}
          {creatives.map((creative) => (
            <RegenerateCreative
              key={creative.code}
              creative={creative}
              book={book}
              setCreatives={setCreatives}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default BookCreatives;
