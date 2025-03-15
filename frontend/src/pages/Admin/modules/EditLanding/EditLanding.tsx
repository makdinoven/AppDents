import s from "./EditLanding.module.scss";
import AdminField from "../common/AdminField/AdminField.tsx";
import { LandingType } from "../../types.ts";
import { t } from "i18next";
import MultiSelect from "../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import PhotoUploader from "../../../../components/CommonComponents/PhotoUploader/PhotoUploader.tsx";

const EditLanding = ({
  landing,
  setLanding,
  authors,
  languages,
  tags,
  courses,
}: {
  authors: any[];
  languages: any[];
  tags: any[];
  courses: any[];
  landing: LandingType;
  setLanding?: any;
}) => {
  const handleChange = (e: any) => {
    const { name, value } = e;
    setLanding((prev: any) => {
      if (!prev) return prev;
      return { ...prev, [name]: value };
    });
  };

  const handleUploadPhoto = (url: string) => {
    setLanding((prev: any) => {
      if (!prev) return prev;
      return { ...prev, preview_photo: url };
    });
  };

  return (
    <div className={s.edit_landing}>
      <AdminField
        type="input"
        id="landing_name"
        placeholder={t("admin.landings.title.placeholder")}
        label={t("admin.landings.title")}
        value={landing.landing_name}
        onChange={handleChange}
      />
      <AdminField
        type="textarea"
        id="course_program"
        placeholder={t("admin.landings.courseProgram.placeholder")}
        label={t("admin.landings.courseProgram")}
        value={landing.course_program}
        onChange={handleChange}
      />
      <AdminField
        type="input"
        id="page_name"
        placeholder={t("admin.landings.pageName.placeholder")}
        label={t("admin.landings.pageName")}
        value={landing.page_name}
        onChange={handleChange}
      />
      <PhotoUploader
        onUpload={handleUploadPhoto}
        url={landing.preview_photo}
        id="preview_photo"
        title={t("admin.landings.mainImage")}
        label={t("admin.landings.mainImage.choose")}
      />
      <div className={s.selects}>
        <AdminField
          type="input"
          inputType="number"
          id="old_price"
          label={t("admin.landings.oldPrice")}
          placeholder="0"
          value={landing.old_price ?? ""}
          onChange={handleChange}
        />
        <AdminField
          type="input"
          inputType="number"
          id="new_price"
          placeholder="0"
          label={t("admin.landings.price")}
          value={landing.new_price ?? ""}
          onChange={handleChange}
        />
        <AdminField
          type="input"
          inputType="number"
          id="sales_count"
          placeholder="0"
          label={t("admin.landings.salesCount")}
          value={landing.sales_count ?? ""}
          onChange={handleChange}
        />
        <AdminField
          type="input"
          id="lessons_count"
          placeholder={t("admin.landings.lessonsCount.placeholder")}
          label={t("admin.landings.lessonsCount")}
          value={landing.lessons_count ?? ""}
          onChange={handleChange}
        />
        <AdminField
          type="input"
          id="duration"
          placeholder={t("admin.landings.duration.placeholder")}
          label={t("admin.landings.duration")}
          value={landing.duration ?? ""}
          onChange={handleChange}
        />
        <MultiSelect
          isSearchable={false}
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
        id={"course_ids"}
        options={courses}
        placeholder={"Choose an course"}
        label={t("admin.landings.courses")}
        selectedValue={landing.course_ids}
        isMultiple={true}
        onChange={handleChange}
        valueKey="id"
        labelKey="name"
      />
      <MultiSelect
        id={"tag_ids"}
        options={tags}
        placeholder={"Choose a tag"}
        label={t("admin.landings.tags")}
        selectedValue={landing.tag_ids}
        isMultiple={true}
        onChange={handleChange}
        valueKey="id"
        labelKey="name"
      />
      <MultiSelect
        id={"author_ids"}
        options={authors}
        placeholder={"Choose an author"}
        label={t("admin.landings.authors")}
        selectedValue={landing.author_ids}
        isMultiple={true}
        onChange={handleChange}
        valueKey="id"
        labelKey="name"
      />
    </div>
  );
};

export default EditLanding;
