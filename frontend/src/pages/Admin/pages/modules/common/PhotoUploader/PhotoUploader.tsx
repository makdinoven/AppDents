import s from "./PhotoUploader.module.scss";
import initialPhoto from "../../../../../../assets/no-pictures.png";
import { useState } from "react";

const PhotoUploader = ({
  id,
  title,
  label,
  url,
}: {
  id: string;
  title: string;
  label: string;
  url: string;
}) => {
  const [preview, setPreview] = useState(url || initialPhoto);

  const uploadPhoto = (e: any) => {
    const file = e.target.files?.[0];
    if (file) {
      const objectUrl = URL.createObjectURL(file);
      setPreview(objectUrl);
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
