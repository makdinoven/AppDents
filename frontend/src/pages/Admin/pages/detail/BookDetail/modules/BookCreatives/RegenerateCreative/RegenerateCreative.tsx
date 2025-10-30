import s from "./RegenerateCreative.module.scss";
import PrettyButton from "../../../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Creative } from "../BookCreatives.tsx";
import { useState } from "react";
import { Alert } from "../../../../../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../../../../../assets/icons";
import LoaderOverlay from "../../../../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import AdminField from "../../../../../modules/common/AdminField/AdminField.tsx";
import { adminApi } from "../../../../../../../../api/adminApi/adminApi.ts";

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
      const updatedCreative = res.data.items[0];
      setCreatives((prev: any) =>
        prev
          ? prev.map((item: Creative) =>
              item.code === creative.code ? updatedCreative : item,
            )
          : [updatedCreative],
      );
      Alert("Creative  regenerated", <CheckMark />);
      setLoading(false);
    } catch (error) {
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
