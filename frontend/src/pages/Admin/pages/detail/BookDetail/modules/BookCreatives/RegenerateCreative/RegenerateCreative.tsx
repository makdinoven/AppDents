import s from "./RegenerateCreative.module.scss";
import PrettyButton from "../../../../../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import { Creative } from "../BookCreatives.tsx";
import { useState } from "react";
import { Alert } from "../../../../../../../../shared/components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../../shared/assets/icons";
import LoaderOverlay from "../../../../../../../../shared/components/ui/LoaderOverlay/LoaderOverlay.tsx";
import AdminField from "../../../../../modules/common/AdminField/AdminField.tsx";
import { adminApi } from "../../../../../../../../shared/api/adminApi/adminApi.ts";

const RegenerateCreative = ({
  creative,
  setCreatives,
  book,
}: {
  creative: Creative;
  book: any;
  setCreatives: (creatives: any) => void;
}) => {
  const [showInputs, setShowInputs] = useState(false);
  const [loading, setLoading] = useState(false);
  const [layers, setLayers] = useState<Record<string, any>>(
    creative.payload_used?.layers || {},
  );

  const handleChange = (key: string, value: string) => {
    setLayers((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        ...(prev[key].text !== undefined ? { text: value } : { image: value }),
      },
    }));
  };

  const handleGetStatus = async (task_id: number) => {
    try {
      const res = await adminApi.getBookCreativesStatus(task_id);
      if (res.data.state === "error") {
        setLoading(false);
        Alert(`Error: ${res.data.error}`, <ErrorIcon />);
      }

      if (res.data.state === "done") {
        const items = res.data.result.items;
        setCreatives(items);
        Alert("Creative regenerated", <CheckMark />);
        setLoading(false);
      }

      return res.data.state;
    } catch (e: any) {
      console.error("Status polling error:", e);
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

  const handleRegenerateCreative = async (creative: Creative) => {
    const params = {
      book_id: book.id,
      target: creative.code,
    };

    const data = {
      language: book.language,
      fields: {
        layers: layers,
      },
    };

    try {
      setLoading(true);
      const res = await adminApi.createBookCreativesManual(params, data);
      if (res.data.overall === "ready") {
        setCreatives(res.data.items);
        Alert("Creative regenerated", <CheckMark />);
        setLoading(false);
        return;
      }
      if (res.data.task_id) {
        pollStatus(res.data.task_id);
      }
    } catch (error: any) {
      Alert(`Error regenerating creative: ${error}`, <ErrorIcon />);
      setLoading(false);
    }
  };

  return (
    <div className={s.creative_container}>
      {loading && <LoaderOverlay />}
      <div className={s.img_wrapper}>
        {<p>{showInputs ? "hide inputs" : "regenerate"}</p>}

        <img
          onClick={() => setShowInputs(!showInputs)}
          src={creative.s3_url}
          alt={creative.code}
        />
      </div>

      {showInputs && (
        <>
          <div className={s.inputs_container}>
            {Object.entries(layers).map(([key, value]) => (
              <AdminField
                key={key}
                label={key}
                id={key}
                type={key.includes("description") ? "textarea" : "input"}
                value={value.text || value.image || ""}
                onChange={(e: any) => handleChange(key, e.value)}
              />
            ))}
          </div>
          <PrettyButton
            variant={"danger"}
            text={"regenerate"}
            onClick={() => handleRegenerateCreative(creative)}
          />
        </>
      )}
    </div>
  );
};

export default RegenerateCreative;
