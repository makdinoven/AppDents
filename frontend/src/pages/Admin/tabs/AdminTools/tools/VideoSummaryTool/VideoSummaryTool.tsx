import s from "./VideoSummaryTool.module.scss";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../../../components/ui/Alert/Alert.tsx";
import { Trans } from "react-i18next";
import AdminField from "../../../../modules/common/AdminField/AdminField.tsx";
import { t } from "i18next";
import PrettyButton from "../../../../../../components/ui/PrettyButton/PrettyButton.tsx";

export type SummaryToolDataType = {
  video_url: string;
  context: string | null;
  answer_format: string | null;
};

const VideoSummaryTool = () => {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [dataToSend, setDataToSend] = useState<SummaryToolDataType>({
    video_url: "",
    context: null,
    answer_format: null,
  });
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);

  const getSummary = async () => {
    if (!dataToSend.video_url) {
      Alert("Enter source URL");
      return;
    }

    try {
      setLoading(true);
      setSummary(null);
      const res = await adminApi.getVideoSummary(dataToSend);
      setJobId(res.data.task_id);
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
        const res = await adminApi.getVideoSummaryStatus(jobId);
        setJobStatus(res.data.state);
        if (res.data.state === "SUCCESS") {
          setJobStatus("");
          setSummary(res.data.result.summary);
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

  const handleInputChange = (
    e: any,
    field: "video_url" | "context" | "answer_format",
  ) => {
    setDataToSend((prev) => ({
      ...prev,
      [field]: e.value,
    }));
    if (summary && field === "video_url") setSummary(null);
  };

  const handleCopy = async () => {
    if (!summary) return;
    try {
      await navigator.clipboard.writeText(summary);
      Alert("Successfully copied to clipboard");
    } catch (err) {
      console.error("Не удалось скопировать ссылку:", err);
    }
  };

  const handleClear = () => {
    setSummary(null);
    setDataToSend({
      video_url: "",
      context: null,
      answer_format: null,
    });
  };

  return (
    <div className={s.tool_container}>
      <h2 className={s.tool_title}>
        <Trans i18nKey={"admin.tools.videoSummary.title"} />
      </h2>
      <div className={s.enter_url_container}>
        <div className={s.input}>
          <AdminField
            id={"video_summary_src_url"}
            type={"input"}
            inputType={"string"}
            label={t("admin.tools.videoSummary.label")}
            placeholder={t("admin.tools.videoSummary.placeholder")}
            value={dataToSend.video_url}
            onChange={(e) => handleInputChange(e, "video_url")}
          />
        </div>
        {!summary && (
          <>
            <div className={s.input}>
              <AdminField
                id={"video_summary_context"}
                type={"textarea"}
                inputType={"string"}
                label={t("admin.tools.videoSummary.context.label")}
                placeholder={t("admin.tools.videoSummary.context.placeholder")}
                value={dataToSend.context ? dataToSend.context : ""}
                onChange={(e) => handleInputChange(e, "context")}
              />
            </div>
            <div className={s.input}>
              <AdminField
                id={"video_summary_answer"}
                type={"textarea"}
                inputType={"string"}
                label={t("admin.tools.videoSummary.answer.label")}
                placeholder={t("admin.tools.videoSummary.answer.placeholder")}
                value={dataToSend.answer_format ? dataToSend.answer_format : ""}
                onChange={(e) => handleInputChange(e, "answer_format")}
              />
            </div>
          </>
        )}
      </div>

      <PrettyButton
        className={jobStatus ? s[jobStatus.toLowerCase()] : ""}
        text={
          !jobStatus
            ? summary
              ? "clear"
              : "admin.tools.videoSummary.getSummary"
            : jobStatus
        }
        variant={"default"}
        onClick={!loading ? (summary ? handleClear : getSummary) : undefined}
        loading={loading}
      />

      {summary && (
        <div className={s.text}>
          <p>{summary}</p>
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

export default VideoSummaryTool;
