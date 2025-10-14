import s from "./MagicVideoTool.module.scss";
import { Alert } from "../../../../../components/ui/Alert/Alert.tsx";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import AdminField from "../../modules/common/AdminField/AdminField.tsx";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { CheckMark, ErrorIcon } from "../../../../../assets/icons";

const MagicVideoTool = () => {
  const [loading, setLoading] = useState(false);
  const [srcUrl, setSrcUrl] = useState<string>("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskState, setTaskState] = useState<string | null>(null);

  const handleInputChange = (e: any) => {
    if (loading) return;
    setSrcUrl(e.value);
  };

  const fixVideo = async () => {
    if (!srcUrl) {
      Alert("Enter source URL");
      return;
    }

    const dataToSend = {
      video_url: srcUrl,
      prefer_new: true,
      sync: false,
    };

    try {
      setLoading(true);
      const res = await adminApi.validateVideoFix(dataToSend);
      setTaskId(res.data.task_id);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const res = await adminApi.getValidateVideoFixStatus(taskId);
        setTaskState(res.data.state);
        if (res.data.state.toLowerCase() === "success") {
          Alert("Video fixed successfully", <CheckMark />);
          setSrcUrl("");
          setTaskState("");
          setLoading(false);
          clearInterval(interval);
        }
      } catch (e) {
        Alert("Error. Video was not fixed", <ErrorIcon />);
        console.error(e);
        setLoading(false);
        clearInterval(interval);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <div className={s.magic_tool}>
      <div className={s.input}>
        <AdminField
          id={"magic_video_tool"}
          type={"input"}
          inputType={"string"}
          label={"Video URL *"}
          placeholder={"Enter video URL..."}
          value={srcUrl}
          onChange={handleInputChange}
        />
      </div>

      <PrettyButton
        className={taskState ? s[taskState.toLowerCase()] : ""}
        text={!taskState ? "fix video" : taskState}
        variant={"default"}
        onClick={!loading ? fixVideo : undefined}
        loading={loading}
      />
    </div>
  );
};

export default MagicVideoTool;
