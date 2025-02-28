import s from "../CourseDetail/CourseDetail.module.scss";
import { SectionType } from "../../types.ts";
import { useState } from "react";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import AdminField from "../CourseDetail/modules/AdminField/AdminField.tsx";
import { Trans } from "react-i18next";
import { t } from "i18next";

const EditSection = ({
  section,
  children,
  index,
  defaultOpen = false,
  handleDelete,
  setCourse,
}: {
  section: SectionType;
  index?: number;
  setCourse: any;
  children?: React.ReactNode;
  defaultOpen?: boolean;
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

      const updatedSections = prev.sections.map((s: any) =>
        s.id === section.id ? { ...s, [name]: value } : s,
      );

      return { ...prev, sections: updatedSections };
    });
  };

  return (
    <>
      {!isOpen ? (
        <div className={s.section_closed}>
          <div className={s.section_name}>
            <Trans i18nKey={"admin.sections.section"} /> {index && index}{" "}
            <span>{section.name}</span>
          </div>
          <PrettyButton text={t("open")} onClick={toggleOpen} />
        </div>
      ) : (
        <div className={s.section}>
          <div className={s.section_header}>
            <PrettyButton
              variant={"danger"}
              text={t("admin.sections.delete")}
              onClick={handleDelete}
            />
            <PrettyButton
              text={t("admin.sections.close")}
              onClick={toggleOpen}
            />
          </div>

          <div className={s.section_name_description}>
            <AdminField
              type="input"
              inputType="text"
              id={"name"}
              label={t("admin.sections.name")}
              value={section.name}
              onChange={(e) => handleChange(e)}
            />
          </div>
          {children}
        </div>
      )}
    </>
  );
};

export default EditSection;
