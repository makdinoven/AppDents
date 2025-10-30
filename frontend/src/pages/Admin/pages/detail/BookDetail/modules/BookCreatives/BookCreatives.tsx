import s from "./BookCreatives.module.scss";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";
import PrettyButton from "../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useState } from "react";
import LoaderOverlay from "../../../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import RegenerateCreative from "./RegenerateCreative/RegenerateCreative.tsx";

export type Creative = {
  code: string;
  creative_code: string;
  status: string;
  s3_url: string;
  payload_used: { layers: any };
};

const BookCreatives = ({ book }: { book: any }) => {
  const [loading, setLoading] = useState(false);
  const [creatives, setCreatives] = useState<null | Creative[]>(null);

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
      // Alert("Creatives created", <CheckMark />);
      setCreatives(res.data.items);
      setLoading(false);
    } catch {
      // Alert(`Error creating creative: ${error}`, <ErrorIcon />);
      setLoading(false);
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
