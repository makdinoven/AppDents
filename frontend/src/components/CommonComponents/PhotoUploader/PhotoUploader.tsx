import s from "./PhotoUploader.module.scss";
import initialPhoto from "../../../assets/no-pictures.png";
import { useEffect, useState } from "react";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import { Alert } from "../../ui/Alert/Alert.tsx";
import { ErrorIcon } from "../../../assets/icons";

const PhotoUploader = ({
  id,
  title,
  label,
  url,
  onUpload,
  type = "default",
  dataId,
}: {
  type?: "default" | "book";
  id: string;
  title: string;
  label: string;
  dataId?: number;
  url: string | undefined;
  onUpload: any;
}) => {
  const [preview, setPreview] = useState(url || initialPhoto);

  useEffect(() => {
    if (url) {
      setPreview(url);
    }
  }, [url]);

  const uploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        let res;

        if (type === "book") {
          const formData = new FormData();
          formData.append("file", file);
          formData.append("entity_type", "book_cover");
          formData.append("entity_id", String(dataId!));

          res = await adminApi.uploadImageNew(formData);
        } else {
          const formData = new FormData();
          formData.append("file", file);
          res = await adminApi.uploadPhoto(formData);
        }

        const uploadedUrl = res.data.url;
        setPreview(uploadedUrl);
        onUpload(uploadedUrl);
      } catch (error) {
        Alert(`Error loading image: ${error}`, <ErrorIcon />);
      }
    }
  };

  return (
    <div className={s.photo_uploader}>
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
