import s from "./PhotoUploader.module.scss";
import initialPhoto from "../../../assets/no-pictures.png";
import { useState } from "react";
import { adminApi } from "../../../api/adminApi/adminApi.ts";

const PhotoUploader = ({
  id,
  title,
  label,
  url,
  onUpload,
}: {
  id: string;
  title: string;
  label: string;
  url: string | undefined;
  onUpload: any;
}) => {
  const [preview, setPreview] = useState(url || initialPhoto);

  const uploadPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await adminApi.uploadPhoto(formData);
        const uploadedUrl = res.data.url;
        setPreview(uploadedUrl);
        onUpload(uploadedUrl);
      } catch (error) {
        console.error("Ошибка загрузки фото:", error);
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
