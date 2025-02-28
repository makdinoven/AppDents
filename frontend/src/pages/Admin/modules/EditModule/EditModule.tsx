import s from "../CourseDetail/CourseDetail.module.scss";
import { ModuleType, SectionType } from "../../types.ts";
import { useState } from "react";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import AdminField from "../CourseDetail/modules/AdminField/AdminField.tsx";
import { t } from "i18next";

const EditModule = ({
  section,
  module,
  defaultOpen = false,
  setCourse,
  handleDelete,
}: {
  section: SectionType;
  module: ModuleType;
  defaultOpen?: boolean;
  index?: number;
  setCourse: any;
  handleDelete: any;
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
  };

  const handleChange = (e: any) => {
    const { name, value } = e;
    setCourse((prev: any) => {
      if (!prev) return prev;

      return {
        ...prev,
        sections: prev.sections.map((s: any) =>
          s.id === section.id
            ? {
                ...s,
                modules: s.modules.map((m: any) =>
                  m.id === module.id ? { ...m, [name]: value } : m,
                ),
              }
            : s,
        ),
      };
    });
  };

  return (
    <>
      {!isOpen ? (
        <div className={s.section_closed}>
          <div className={s.section_name}>
            <span>{module.title}</span>
          </div>
          <PrettyButton text={t("open")} onClick={toggleOpen} />
        </div>
      ) : (
        <div className={s.module} key={module.id}>
          <div className={s.section_header}>
            <PrettyButton
              variant={"danger"}
              text={t("admin.modules.delete")}
              onClick={handleDelete}
            />
            <PrettyButton
              text={t("admin.modules.close")}
              onClick={toggleOpen}
            />
          </div>
          <AdminField
            type="input"
            inputType="text"
            id={"title"}
            label={t("admin.modules.title")}
            value={module.title}
            onChange={(e) => handleChange(e)}
          />
          <AdminField
            type="input"
            inputType="text"
            id={"duration"}
            label={t("admin.modules.duration")}
            value={module.duration}
            onChange={(e) => handleChange(e)}
          />
          <AdminField
            type="textarea"
            inputType="text"
            id={"program_text"}
            label={t("admin.modules.programText")}
            value={module.program_text}
            onChange={(e) => handleChange(e)}
          />
          <AdminField
            type="input"
            inputType="text"
            id={"short_video_link"}
            label={t("admin.modules.shortLink")}
            value={module.short_video_link}
            onChange={(e) => handleChange(e)}
          />
          <AdminField
            type="input"
            inputType="text"
            id={"full_video_link"}
            label={t("admin.modules.fullLink")}
            value={module.full_video_link}
            onChange={(e) => handleChange(e)}
          />
        </div>
      )}
    </>
  );
};

export default EditModule;
