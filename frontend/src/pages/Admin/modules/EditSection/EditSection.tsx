import { useState } from "react";
import { SectionType } from "../../types.ts";
import CollapsibleSection from "../common/CollapsibleSection/CollapsibleSection.tsx";

const EditSection = ({
  section,
  children,
  handleDelete,
  setCourse,
  moveSectionUp,
  moveSectionDown,
}: {
  section: SectionType;
  setCourse: any;
  children?: React.ReactNode;
  handleDelete: any;
  moveSectionUp: () => void;
  moveSectionDown: () => void;
}) => {
  const [isOpen, setIsOpen] = useState(false);

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
    <CollapsibleSection
      title="admin.sections"
      handleMoveToTop={moveSectionUp}
      handleMoveToBottom={moveSectionDown}
      data={{
        id: section.id,
        name: section.section_name,
        section_name: section.section_name,
      }}
      fields={[
        {
          id: "section_name",
          label: "name",
          placeholder: "name.placeholder",
          type: "text",
        },
      ]}
      isOpen={isOpen}
      toggleOpen={toggleOpen}
      handleDelete={handleDelete}
      onChange={handleChange}
    >
      {children}
    </CollapsibleSection>
  );
};

export default EditSection;
