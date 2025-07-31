import s from "./AdminTools.module.scss";
import { useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import AdminField from "../../modules/common/AdminField/AdminField.tsx";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import { Alert } from "../../../../components/ui/Alert/Alert.tsx";
import { Trans } from "react-i18next";
import Loader from "../../../../components/ui/Loader/Loader.tsx";

const AdminTools = () => {
  const [loading, setLoading] = useState(false);
  const [clipUrl, setClipUrl] = useState<string | null>(null);
  const [srcUrl, setSrcUrl] = useState<string>("");

  const getClip = async () => {
    setLoading(true);
    setClipUrl(null);
    try {
      const res = await adminApi.getClip(srcUrl);
      setClipUrl(res.data.clip_url);
      setLoading(false);
    } catch (e) {
      setLoading(false);
      console.error(e);
    }
  };

  const handleInputChange = (e: any) => {
    setSrcUrl(e.value);
    if (clipUrl) {
      setClipUrl(null);
    }
  };

  const handleCopy = async () => {
    if (clipUrl) {
      try {
        await navigator.clipboard.writeText(clipUrl);
        Alert(`Successfully copied to clipboard`);
      } catch (err) {
        console.error("Не удалось скопировать ссылку:", err);
      }
    }
  };

  return (
    <>
      <div className={s.enter_url_container}>
        <div className={s.input}>
          <AdminField
            id={"src_url"}
            type={"input"}
            inputType={"string"}
            placeholder={t("admin.tools.clip.placeholder")}
            label={t("admin.tools.clip.label")}
            value={srcUrl}
            onChange={(e: any) => handleInputChange(e)}
          />
        </div>

        <PrettyButton
          text={"admin.tools.clip.getClip"}
          variant={"default"}
          onClick={!loading ? getClip : null}
          loading={loading}
        />
      </div>

      <div className={s.clip_url_container}>
        {loading && <Loader />}
        {clipUrl && (
          <>
            <div className={s.clip_container}>
              <p className={s.clip_url_label}>
                <Trans i18nKey={"admin.tools.clip.yourClipUrl"} />
              </p>
              <a
                target="_blank"
                rel="noopener noreferrer"
                href={clipUrl}
                className={s.clip_url}
              >
                {clipUrl}
              </a>
            </div>
            <PrettyButton
              text={"copy"}
              variant={"primary"}
              onClick={handleCopy}
            />
          </>
        )}
      </div>
    </>
  );
};

export default AdminTools;
