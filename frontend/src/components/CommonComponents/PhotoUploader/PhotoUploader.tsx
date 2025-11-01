import s from "./PhotoUploader.module.scss";
import initialPhoto from "../../../assets/no-pictures.png";
import { useEffect, useState } from "react";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import { Alert } from "../../ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../assets/icons";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";

const PhotoUploader = ({
  id,
  title,
  label,
  url,
  onUpload,
  entityType,
  entityId,
}: {
  entityType:
    | "book_cover"
    | "book_landing_preview"
    | "book_landing_galary"
    | "book_landing_gallery"
    | "landing_preview"
    | "author_preview";
  id: string;
  title: string;
  label: string;
  entityId: number;
  url: string | undefined;
  onUpload: any;
}) => {
  const [preview, setPreview] = useState(url || initialPhoto);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (url) {
      setPreview(url);
    }
  }, [url]);

  const uploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        setLoading(true);
        const formData = new FormData();
        formData.append("file", file);
        formData.append("entity_type", entityType);
        formData.append("entity_id", String(entityId));

        const res = await adminApi.uploadImageNew(formData);

        const uploadedUrl = res.data.url;
        setPreview(uploadedUrl);
        onUpload(uploadedUrl);
        setLoading(false);
      } catch (error) {
        setLoading(false);
        Alert(`Error loading image: ${error}`, <ErrorIcon />);
      }
    }
  };

  return (
    <div className={s.photo_uploader}>
      {loading && <LoaderOverlay />}

      <div className={s.input_wrapper}>
        <p>{title}</p>
        <label htmlFor={id}>{label}</label>

        <input
          accept="image/png, image/jpeg"
          onChange={uploadPhoto}
          name={id}
          id={id}
          type="file"
        />
      </div>
      <div className={s.photo_preview}>
        <img src={preview} alt="Landing main photo" />
      </div>
    </div>
  );
};

export default PhotoUploader;
