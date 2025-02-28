import s from "../CourseDetail/CourseDetail.module.scss";
import { Trans } from "react-i18next";
import AdminField from "../CourseDetail/modules/AdminField/AdminField.tsx";
import { t } from "i18next";
import { CourseType } from "../../types.ts";

const EditCourse = ({
  course,
  setCourse,
}: {
  course: CourseType;
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
    <>
      <div className={s.course_name_description}>
        <h1>
          <Trans i18nKey={"admin.courses.update"} />
        </h1>
        <AdminField
          type="input"
          inputType="text"
          id="name"
          label={t("admin.courses.name")}
          value={course?.name}
          onChange={handleChange}
        />
        <AdminField
          type="textarea"
          inputType="text"
          id="description"
          label={t("admin.courses.description")}
          value={course?.description}
          onChange={handleChange}
        />
      </div>
    </>
  );
};

export default EditCourse;
