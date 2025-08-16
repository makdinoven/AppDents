import { useEffect, useState } from "react";
import s from "./ClipTool.module.scss";
import AdminField from "../../../../modules/common/AdminField/AdminField.tsx";
import { t } from "i18next";
import PrettyButton from "../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import Loader from "../../../../../../components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";
import { adminApi } from "../../../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../../../components/ui/Alert/Alert.tsx";

const ClipTool = () => {
  const [loading, setLoading] = useState(false);
  const [clipUrl, setClipUrl] = useState<string | null>(null);
  const [srcUrl, setSrcUrl] = useState<string>("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const getClip = async () => {
    setLoading(true);
    setClipUrl(null);
    try {
      const res = await adminApi.getClip(srcUrl);
      setJobId(res.data.job_id);
      setJobStatus(res.data.status);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const res = await adminApi.getClipStatus(jobId);
        console.log(jobStatus);
        setJobStatus(res.data.status);
        if (res.data.status === "done") {
          setJobStatus("");
          setClipUrl(res.data.clip_url);
          setLoading(false);
          clearInterval(interval);
        }
      } catch (e) {
        setJobStatus("error");
        console.error(e);
        setLoading(false);
        clearInterval(interval);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobId]);

  const handleInputChange = (e: any) => {
    setSrcUrl(e.value);
    if (clipUrl) setClipUrl(null);
  };

  const handleCopy = async () => {
    if (!clipUrl) return;
    try {
      await navigator.clipboard.writeText(clipUrl);
      Alert("Successfully copied to clipboard");
    } catch (err) {
      console.error("Не удалось скопировать ссылку:", err);
    }
  };

  return (
    <div className={s.clip_tool}>
      <h2 className={s.tool_title}>
        <Trans i18nKey={"admin.tools.clip.title"} />
      </h2>
      <div className={s.enter_url_container}>
        <div className={s.input}>
          <AdminField
            id={"src_url"}
            type={"input"}
            inputType={"string"}
            label={t("admin.tools.clip.label")}
            placeholder={t("admin.tools.clip.placeholder")}
            value={srcUrl}
            onChange={handleInputChange}
          />
        </div>

        <PrettyButton
          className={jobStatus ? s[jobStatus] : ""}
          text={!jobStatus ? "admin.tools.clip.getClip" : jobStatus}
          variant={"default"}
          onClick={!loading ? getClip : undefined}
          loading={loading}
        />
      </div>
      {loading && <Loader />}

      {clipUrl && (
        <div className={s.clip_url_container}>
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
        </div>
      )}
    </div>
  );
};

export default ClipTool;
