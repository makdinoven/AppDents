import s from "./EditCourse.module.scss";
import AdminField from "../common/AdminField/AdminField.tsx";
import { t } from "i18next";

const EditCourse = ({
  course,
  setCourse,
}: {
  course: any;
  setCourse?: any;
}) => {
  const handleChange = (e: any) => {
    const { name, value } = e;

    setCourse((prev: any) => {
      if (!prev) return prev;
      return { ...prev, [name]: value };
    });
  };

  return (
    <div className={s.edit_course}>
      <AdminField
        type="input"
        inputType="text"
        id="course_name"
        label={t("admin.courses.name")}
        placeholder={t("admin.courses.name.placeholder")}
        value={course?.course_name}
        onChange={handleChange}
      />
      <AdminField
        type="textarea"
        inputType="text"
        id="course_description"
        placeholder={t("admin.courses.description.placeholder")}
        label={t("admin.courses.description")}
        value={course?.course_description}
        onChange={handleChange}
      />
    </div>
  );
};

export default EditCourse;
