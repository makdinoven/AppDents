import s from "./BookUploader.module.scss";
import { Alert } from "../../../../../../../components/ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../../../../../assets/icons";
import { adminApi } from "../../../../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import LoaderOverlay from "../../../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import ViewLink from "../../../../../../../components/ui/ViewLink/ViewLink.tsx";

type JobStatus = "pending" | "running" | "success" | "failed" | "skipped";

const BookUploader = ({
  itemId,
  files,
  setBook,
}: {
  itemId: number;
  setBook: (book: any) => void;
  files: {
    file_format: "PDF" | "EPUB" | "MOBI" | "AZW3" | "FB2";
    size_bytes: number;
    s3_url: string;
  }[];
}) => {
  const [loading, setLoading] = useState(false);
  const [previewStatus, setPreviewStatus] = useState<JobStatus | null>(null);
  const [formatStatus, setFormatStatus] = useState<JobStatus | null>(null);
  const [bookUrl, setBookUrl] = useState("");

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf") {
      Alert("Please select a valid PDF file", <ErrorIcon />);
      return;
    }

    loadPdf(file);
  };

  const loadPdf = async (file: File) => {
    try {
      setLoading(true);
      setFormatStatus(null);
      setPreviewStatus(null);
      const data = {
        filename: file.name,
        content_type: "application/pdf",
      };
      const res = await adminApi.generatePreSignedPostForPdf(itemId, data);
      const fields = res.data.fields;
      const url = res.data.url;
      const key = res.data.key;

      const formData = new FormData();
      if (fields) {
        Object.entries(fields).forEach(([key, value]) => {
          formData.append(key, value as string);
        });
      }
      formData.append("file", file);

      const uploadResponse = await fetch(url, {
        method: "POST",
        body: formData,
      });
      if (!uploadResponse.ok) {
        throw new Error("Upload failed");
      }

      const finalizeRes = await adminApi.finalizeBookUploading(itemId, { key });
      setBook((prev: any) => ({
        ...prev,
        files: [
          {
            file_format: "PDF",
            size_bytes: finalizeRes.data.size_bytes,
            s3_url: finalizeRes.data.pdf_cdn_url,
          },
        ],
      }));

      fetchStatuses();
      fetchPreviews();
      setBookUrl(finalizeRes.data.pdf_cdn_url);
    } catch (e) {
      Alert(`Error uploading pdf file: ${e}`, <ErrorIcon />);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatuses = async () => {
    try {
      const format = await adminApi.getBookFormatStatus(itemId);
      setFormatStatus(format.data.job.status as JobStatus);
    } catch (e) {
      console.error("Error fetching statuses", e);
    }
  };

  const fetchPreviews = async () => {
    try {
      const preview = await adminApi.getBookPreviewStatus(itemId);
      setPreviewStatus(preview.data.job.status as JobStatus);
    } catch (e) {
      console.error("Error fetching previews", e);
    }
  };

  const updateBookWithFormats = async () => {
    try {
      const res = await adminApi.getBookFormatStatus(itemId);
      const formats = res.data?.formats ?? {};
      const newFiles = Object.entries(formats)
        .filter(
          ([fmt, v]: any) => fmt !== "PDF" && v?.status === "success" && v?.url,
        )
        .map(([fmt, v]: any) => ({
          file_format: fmt as "EPUB" | "MOBI" | "AZW3" | "FB2",
          size_bytes: Number(v.size) || 0,
          s3_url: v.url as string,
        }));
      if (newFiles.length) {
        setBook((prev: any) => {
          const existingPdf = (prev.files ?? []).find(
            (f: any) => f.file_format === "PDF",
          );

          const mergedFiles = existingPdf
            ? [existingPdf, ...newFiles]
            : newFiles;

          return { ...prev, files: mergedFiles };
        });
      }
    } catch (e) {
      console.error("Error updating book formats:", e);
    }
  };

  useEffect(() => {
    if (
      !previewStatus ||
      previewStatus === "success" ||
      previewStatus === "failed"
    ) {
      return;
    }
    const interval = setInterval(fetchPreviews, 3000);
    return () => clearInterval(interval);
  }, [previewStatus]);

  useEffect(() => {
    if (
      !formatStatus ||
      formatStatus === "success" ||
      formatStatus === "failed"
    ) {
      return;
    }
    const interval = setInterval(fetchStatuses, 3000);
    return () => clearInterval(interval);
  }, [formatStatus]);

  useEffect(() => {
    if (formatStatus !== "success") return;
    updateBookWithFormats();
  }, [formatStatus, itemId, setBook]);

  return (
    <div className={s.pdf_uploader_container}>
      <div className={s.uploader_header}>
        <h3>Book Uploader</h3>

        {(previewStatus || formatStatus) && (
          <div className={s.statuses}>
            {previewStatus && (
              <p className={`${s.preview_status} ${s[previewStatus]}`}>
                {previewStatus === "success"
                  ? "Preview generated"
                  : `Generating preview... ${previewStatus}`}
              </p>
            )}
            {formatStatus && (
              <p className={`${s.format_status} ${s[formatStatus]}`}>
                {formatStatus === "success"
                  ? "Formats generated"
                  : `Generating formats... ${formatStatus}`}
              </p>
            )}
          </div>
        )}
      </div>

      {files && (
        <ul className={s.files_list}>
          {files.map((file) => (
            <li key={file.file_format}>
              <a href={file.s3_url} target="_blank" rel="noopener noreferrer">
                {file.file_format}
                <span>{file.size_bytes}</span>
              </a>
            </li>
          ))}
        </ul>
      )}

      <div className={s.uploader_middle}>
        <div className={s.input_wrapper}>
          {loading && <LoaderOverlay />}
          <label className={s.custom_button}>
            Upload Book
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              disabled={loading}
              className={s.hidden_input}
            />
          </label>
        </div>
        {bookUrl && (
          <ViewLink
            text={"View generated pdf book"}
            className={s.view_link}
            link={bookUrl}
            isExternal
          />
        )}
      </div>
    </div>
  );
};

export default BookUploader;
