import s from "./DetailPage.module.scss";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import { useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import MultiSelect from "../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { t } from "i18next";
import { LANGUAGES } from "../../../common/helpers/commonConstants.ts";
import AdminField from "../modules/common/AdminField/AdminField.tsx";
import PhotoUploader from "../../../components/CommonComponents/PhotoUploader/PhotoUploader.tsx";
import { AuthorType } from "../types.ts";
import Loader from "../../../components/ui/Loader/Loader.tsx";
import { Alert } from "../../../components/ui/Alert/Alert.tsx";
import ErrorIcon from "../../../assets/icons/ErrorIcon.tsx";

const AuthorDetail = () => {
  const [loading, setLoading] = useState(true);
  const [author, setAuthor] = useState<AuthorType | null>(null);
  const navigate = useNavigate();
  const { authorId } = useParams();

  useEffect(() => {
    if (authorId) {
      fetchData(authorId);
    }
  }, [authorId]);

  const fetchData = async (authorId: any) => {
    try {
      const res = await adminApi.getAuthor(authorId);
      setAuthor(res.data);
      setLoading(false);
    } catch (error: any) {
      Alert(
        `Error fetching author data, error message: ${error.message}`,
        <ErrorIcon />
      );
    }
  };

  const handleUploadPhoto = (url: string) => {
    setAuthor((prev: any) => {
      if (!prev) return prev;
      return { ...prev, photo: url };
    });
  };

  const handleChange = (e: any) => {
    const { name, value } = e;
    setAuthor((prev: any) => {
      if (!prev) return prev;
      return { ...prev, [name]: value };
    });
  };

  const handleSave = async () => {
    try {
      await adminApi.updateAuthor(authorId, author);
      navigate(-1);
    } catch (error) {
      console.error("Error updating author:", error);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete this author?`)) return;
    try {
      await adminApi.deleteAuthor(authorId);
      navigate(-1);
    } catch (error) {
      console.error("Error deleting author:", error);
    }
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.authors.edit"} />
      {loading ? (
        <Loader />
      ) : (
        <>
          <div className={s.list}>
            <AdminField
              type="input"
              id="name"
              placeholder={t("admin.authors.name.placeholder")}
              label={t("admin.authors.name")}
              value={author?.name}
              onChange={handleChange}
            />
            <AdminField
              type="textarea"
              id="description"
              placeholder={t("admin.authors.description.placeholder")}
              label={t("admin.authors.description")}
              value={author?.description}
              onChange={handleChange}
            />
            <MultiSelect
              isSearchable={false}
              id={"language"}
              options={LANGUAGES}
              placeholder={"Choose a language"}
              label={t("admin.landings.language")}
              selectedValue={author?.language ? author?.language : "EN"}
              isMultiple={false}
              onChange={handleChange}
              valueKey="value"
              labelKey="label"
            />
            <PhotoUploader
              onUpload={handleUploadPhoto}
              url={author?.photo}
              id="photo"
              title={t("admin.authors.photo")}
              label={t("admin.authors.photo.placeholder")}
            />
          </div>

          <DetailBottom
            deleteLabel={"admin.authors.delete"}
            handleSave={handleSave}
            handleDelete={handleDelete}
          />
        </>
      )}
    </div>
  );
};

export default AuthorDetail;
