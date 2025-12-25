import s from "./MagicVideoTool.module.scss";
import { Alert } from "../../../../../shared/components/ui/Alert/Alert.tsx";
import { adminApi } from "../../../../../shared/api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import AdminField from "../../modules/common/AdminField/AdminField.tsx";
import PrettyButton from "../../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import { CheckMark, ErrorIcon } from "../../../../../shared/assets/icons";

interface DiagnosticCheck {
  status: string;
  message: string;
  details: Record<string, any>;
}

interface DiagnosticResult {
  video_url: string;
  s3_key: string;
  overall_status: string;
  checks: Record<string, DiagnosticCheck>;
  recommendations: string[];
}

type TaskType = "fix_hls" | "full_repair" | "force_rebuild" | null;

const MagicVideoTool = () => {
  const [loading, setLoading] = useState(false);
  const [diagnosing, setDiagnosing] = useState(false);
  const [srcUrl, setSrcUrl] = useState<string>("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskType, setTaskType] = useState<TaskType>(null);
  const [taskState, setTaskState] = useState<string | null>(null);
  const [diagnostic, setDiagnostic] = useState<DiagnosticResult | null>(null);
  const [maintenanceResult, setMaintenanceResult] = useState<any | null>(null);

  const handleInputChange = (e: any) => {
    if (loading || diagnosing) return;
    setSrcUrl(e.value);
    setDiagnostic(null); // Сброс диагностики при изменении URL
    setMaintenanceResult(null);
  };

  const diagnoseVideo = async () => {
    if (!srcUrl) {
      Alert("Enter source URL");
      return;
    }

    try {
      setDiagnosing(true);
      setDiagnostic(null);
      const res = await adminApi.diagnoseVideo(srcUrl);
      setDiagnostic(res.data);
    } catch (e) {
      console.error(e);
      Alert("Failed to diagnose video", <ErrorIcon />);
    } finally {
      setDiagnosing(false);
    }
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
      setTaskType("fix_hls");
      const res = await adminApi.validateVideoFix(dataToSend);
      setTaskId(res.data.task_id);
    } catch (e) {
      console.error(e);
      setLoading(false);
      setTaskType(null);
    }
  };

  const fullRepair = async () => {
    if (!srcUrl) {
      Alert("Enter source URL");
      return;
    }

    try {
      setLoading(true);
      setTaskType("full_repair");
      // Новый пайплайн: запускаем video_maintenance (реально, без dry-run)
      const res = await adminApi.runVideoMaintenance({
        videos: [srcUrl],
        dry_run: false,
        delete_old_key: false, // на тестовом этапе НЕ удаляем старый key
      });
      Alert(`Video maintenance started. Task: ${res.data.task_id}`, <CheckMark />);
      setTaskId(res.data.task_id);
    } catch (e) {
      console.error(e);
      Alert("Failed to start full repair", <ErrorIcon />);
      setLoading(false);
      setTaskType(null);
    }
  };

  const forceRebuild = async () => {
    if (!srcUrl) {
      Alert("Enter source URL");
      return;
    }

    try {
      setLoading(true);
      setTaskType("force_rebuild");
      const res = await adminApi.forceRebuildHls(srcUrl);
      Alert(`Rebuild started. Task queued.`, <CheckMark />);
      setTaskId(res.data.task_id);
      console.log("Force rebuild result:", res.data);
    } catch (e) {
      console.error(e);
      Alert("Failed to start force rebuild", <ErrorIcon />);
      setLoading(false);
      setTaskType(null);
    }
  };

  const cleanupBrokenHls = async (dryRun: boolean) => {
    if (!srcUrl) {
      Alert("Enter source URL");
      return;
    }

    try {
      setDiagnosing(true);
      const res = await adminApi.cleanupHls(srcUrl, dryRun);
      const data = res.data;
      
      if (dryRun) {
        if (data.to_delete?.length > 0) {
          Alert(`Found ${data.to_delete.length} broken HLS to delete. Click "Cleanup" again with dry_run=false.`);
        } else {
          Alert("No broken HLS found", <CheckMark />);
        }
      } else {
        Alert(`Deleted ${data.deleted?.length || 0} broken HLS folders`, <CheckMark />);
        // Обновляем диагностику
        setTimeout(() => diagnoseVideo(), 1000);
      }
      
      // Показываем результаты в консоли для отладки
      console.log("Cleanup result:", data);
    } catch (e) {
      console.error(e);
      Alert("Cleanup failed", <ErrorIcon />);
    } finally {
      setDiagnosing(false);
    }
  };

  const fixVideoAcl = async () => {
    if (!srcUrl) {
      Alert("Enter source URL");
      return;
    }

    try {
      setDiagnosing(true);
      const res = await adminApi.fixVideoAcl(srcUrl, false);
      const data = res.data;
      const summary = data.summary || {};
      
      if (summary.fixed > 0) {
        Alert(`Fixed ACL for ${summary.fixed} files`, <CheckMark />);
        // Обновляем диагностику
        setTimeout(() => diagnoseVideo(), 1000);
      } else if (summary.already_public > 0) {
        Alert(`All ${summary.already_public} files already public`, <CheckMark />);
      } else {
        Alert("No HLS files found to fix", <ErrorIcon />);
      }
      
      console.log("Fix ACL result:", data);
    } catch (e) {
      console.error(e);
      Alert("Fix ACL failed", <ErrorIcon />);
    } finally {
      setDiagnosing(false);
    }
  };

  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        // Для Full Repair теперь используем status нового maintenance
        if (taskType === "full_repair") {
          const res = await adminApi.getVideoMaintenanceStatus(taskId);
          setTaskState(res.data.state);
          const st = String(res.data.state || "").toLowerCase();
          if (st === "success") {
            Alert(`Full repair completed successfully`, <CheckMark />);
            setMaintenanceResult(res.data.result);
            setTaskState(null);
            setLoading(false);
            setTaskId(null);
            setTaskType(null);
            clearInterval(interval);
            setTimeout(() => diagnoseVideo(), 2000);
          } else if (st === "failure") {
            Alert(`Full repair failed. Check logs.`, <ErrorIcon />);
            setMaintenanceResult(res.data.result);
            setTaskState(null);
            setLoading(false);
            setTaskId(null);
            setTaskType(null);
            clearInterval(interval);
          }
        } else {
          const res = await adminApi.getValidateVideoFixStatus(taskId);
          setTaskState(res.data.state);
          if (res.data.state.toLowerCase() === "success") {
            const taskLabel = taskType === "force_rebuild" ? "Force rebuild" : "Video fix";
            Alert(`${taskLabel} completed successfully`, <CheckMark />);
            setTaskState(null);
            setLoading(false);
            setTaskId(null);
            setTaskType(null);
            clearInterval(interval);
            setTimeout(() => diagnoseVideo(), 2000);
          } else if (res.data.state.toLowerCase() === "failure") {
            const taskLabel = taskType === "force_rebuild" ? "Force rebuild" : "Video fix";
            Alert(`${taskLabel} failed. Check logs.`, <ErrorIcon />);
            setTaskState(null);
            setLoading(false);
            setTaskId(null);
            setTaskType(null);
            clearInterval(interval);
          }
        }
      } catch (e) {
        Alert("Error checking status", <ErrorIcon />);
        console.error(e);
        setLoading(false);
        setTaskId(null);
        setTaskType(null);
        clearInterval(interval);
      }
    }, 5000); // Проверяем каждые 5 секунд

    return () => clearInterval(interval);
  }, [taskId, taskType]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ok":
      case "healthy":
        return "#4caf50";
      case "warning":
      case "degraded":
        return "#ff9800";
      case "error":
      case "broken":
        return "#f44336";
      default:
        return "#9e9e9e";
    }
  };

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

      <div className={s.buttons_row}>
        <PrettyButton
          text={"Diagnose"}
          variant={"default_white_hover"}
          onClick={!diagnosing && !loading ? diagnoseVideo : undefined}
          loading={diagnosing}
        />
        <PrettyButton
          className={taskState && taskType === "fix_hls" ? s[taskState.toLowerCase()] : ""}
          text={taskType === "fix_hls" && taskState ? taskState : "Fix HLS"}
          variant={"default"}
          onClick={!loading && !diagnosing ? fixVideo : undefined}
          loading={loading && taskType === "fix_hls" && !taskState}
        />
        <PrettyButton
          className={taskState && taskType === "full_repair" ? s[taskState.toLowerCase()] : ""}
          text={taskType === "full_repair" && taskState ? taskState : "Full Repair"}
          variant={"default"}
          onClick={!loading && !diagnosing ? fullRepair : undefined}
          loading={loading && taskType === "full_repair" && !taskState}
        />
        <PrettyButton
          className={taskState && taskType === "force_rebuild" ? s[taskState.toLowerCase()] : ""}
          text={taskType === "force_rebuild" && taskState ? taskState : "Force Rebuild"}
          variant={"danger"}
          onClick={!loading && !diagnosing ? forceRebuild : undefined}
          loading={loading && taskType === "force_rebuild" && !taskState}
        />
        <PrettyButton
          text={"Find Broken HLS"}
          variant={"default_white_hover"}
          onClick={!diagnosing && !loading ? () => cleanupBrokenHls(true) : undefined}
          loading={diagnosing}
        />
        <PrettyButton
          text={"Delete Broken HLS"}
          variant={"danger"}
          onClick={!diagnosing && !loading ? () => cleanupBrokenHls(false) : undefined}
          loading={diagnosing}
        />
        <PrettyButton
          text={"Fix ACL"}
          variant={"default_white_hover"}
          onClick={!diagnosing && !loading ? fixVideoAcl : undefined}
          loading={diagnosing}
        />
      </div>

      {diagnostic && (
        <div className={s.diagnostic_results}>
          <div className={s.diagnostic_header}>
            <h4>Diagnostic Results</h4>
            <span
              className={s.status_badge}
              style={{ backgroundColor: getStatusColor(diagnostic.overall_status) }}
            >
              {diagnostic.overall_status.toUpperCase()}
            </span>
          </div>

          <div className={s.diagnostic_info}>
            <p><strong>S3 Key:</strong> {diagnostic.s3_key}</p>
          </div>

          <div className={s.checks_grid}>
            {Object.entries(diagnostic.checks).map(([name, check]) => (
              <div key={name} className={s.check_item}>
                <div className={s.check_header}>
                  <span
                    className={s.check_status}
                    style={{ backgroundColor: getStatusColor(check.status) }}
                  />
                  <span className={s.check_name}>{name}</span>
                </div>
                <p className={s.check_message}>{check.message}</p>
                {check.details && Object.keys(check.details).length > 0 && (
                  <details className={s.check_details}>
                    <summary>Details</summary>
                    <pre>{JSON.stringify(check.details, null, 2)}</pre>
                  </details>
                )}
              </div>
            ))}
          </div>

          {diagnostic.recommendations.length > 0 && (
            <div className={s.recommendations}>
              <h5>Recommendations:</h5>
              <ul>
                {diagnostic.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {maintenanceResult && (
        <div className={s.diagnostic_results}>
          <div className={s.diagnostic_header}>
            <h4>Maintenance Result</h4>
            <span className={s.status_badge} style={{ backgroundColor: "#4caf50" }}>
              DONE
            </span>
          </div>
          <details className={s.check_details} open>
            <summary>Important fields</summary>
            <pre>
              {JSON.stringify(
                {
                  status: maintenanceResult?.status,
                  dry_run: maintenanceResult?.dry_run,
                  delete_old_key: maintenanceResult?.delete_old_key,
                  first: maintenanceResult?.results?.[0],
                },
                null,
                2,
              )}
            </pre>
          </details>
          <details className={s.check_details}>
            <summary>Full JSON</summary>
            <pre>{JSON.stringify(maintenanceResult, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
};

export default MagicVideoTool;
