import s from "./EditLanding.module.scss";
import AdminField from "../CourseDetail/modules/AdminField/AdminField.tsx";
import { LandingType } from "../../types.ts";
import { Trans } from "react-i18next";
import { t } from "i18next";
import MultiSelect from "../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";
import PhotoUploader from "../PhotoUploader/PhotoUploader.tsx";

const languages = [
  { label: "English", value: "en" },
  { label: "Russian", value: "ru" },
  { label: "Spanish", value: "es" },
];

const EditLanding = ({
  landing,
  setCourse,
}: {
  landing: LandingType;
  setCourse?: any;
}) => {
  const [authors, setAuthors] = useState<any[]>([]);
  const [tags, setTags] = useState<any[]>([]);

  const handleChange = (e: any) => {
    const { name, value } = e;
    setCourse((prev: any) => {
      if (!prev) return prev;
      return { ...prev, landing: { ...prev.landing, [name]: value } };
    });
  };

  const fetchAuthors = async () => {
    try {
      const res = await adminApi.getAuthors();
      setAuthors(res.data);
    } catch (error) {
      console.error("Error fetching authors", error);
    }
  };

  const fetchTags = async () => {
    try {
      const res = await mainApi.getTags();
      setTags(res.data);
    } catch (error) {
      console.error("Error fetching tags", error);
    }
  };

  useEffect(() => {
    fetchAuthors();
    fetchTags();
  }, []);

  return (
    <div className={s.edit_landing}>
      <h2>
        <Trans i18nKey={"admin.landings.edit"} />
      </h2>
      <AdminField
        type="input"
        id="title"
        label={t("admin.landings.title")}
        value={landing.title}
        onChange={handleChange}
      />
      <AdminField
        type="textarea"
        id="main_text"
        label={t("admin.landings.mainText")}
        value={landing.main_text}
        onChange={handleChange}
      />
      <PhotoUploader
        url={landing.main_image}
        id="main_image"
        title={t("admin.landings.mainImage")}
        label={t("admin.landings.mainImage.choose")}
      />
      {/*<AdminField*/}
      {/*  type="input"*/}
      {/*  id="main_image"*/}
      {/*  label={t("admin.landings.mainImage")}*/}
      {/*  value={landing.main_image}*/}
      {/*  onChange={handleChange}*/}
      {/*/>*/}
      <div className={s.selects}>
        <AdminField
          type="input"
          inputType="number"
          id="old_price"
          label={t("admin.landings.oldPrice")}
          value={landing.old_price}
          onChange={handleChange}
        />
        <AdminField
          type="input"
          inputType="number"
          id="price"
          label={t("admin.landings.price")}
          value={landing.price}
          onChange={handleChange}
        />
        <AdminField
          type="input"
          inputType="number"
          id="sales_count"
          label={t("admin.landings.salesCount")}
          value={landing.sales_count}
          onChange={handleChange}
        />
        <MultiSelect
          id={"tag_id"}
          options={tags}
          placeholder={"Choose a tag"}
          label={t("admin.landings.tag")}
          selectedValue={landing.tag_id}
          isMultiple={false}
          onChange={handleChange}
          valueKey="id"
          labelKey="name"
        />
        <MultiSelect
          id={"language"}
          options={languages}
          placeholder={"Choose a language"}
          label={t("admin.landings.language")}
          selectedValue={landing.language}
          isMultiple={false}
          onChange={handleChange}
          valueKey="value"
          labelKey="label"
        />
      </div>
      <MultiSelect
        id={"authors"}
        options={authors}
        placeholder={"Choose an author"}
        label={t("admin.landings.authors")}
        selectedValue={landing.authors}
        isMultiple={true}
        onChange={handleChange}
        valueKey="id"
        labelKey="name"
      />
    </div>
  );
};

export default EditLanding;
