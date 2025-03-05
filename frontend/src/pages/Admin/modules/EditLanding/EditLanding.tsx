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
      return { ...prev, ...prev.landing, [name]: value };
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
        url={landing.preview_photo}
        id="preview_photo"
        title={t("admin.landings.mainImage")}
        label={t("admin.landings.mainImage.choose")}
      />
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
          id="new_price"
          label={t("admin.landings.price")}
          value={landing.new_price}
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
