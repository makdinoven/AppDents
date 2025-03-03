import { LessonType, SectionType } from "../../types.ts";
import { useState } from "react";
import CollapsibleSection from "../common/CollapsibleSection/CollapsibleSection.tsx";

const EditLesson = ({
  type = "course",
  section,
  lesson,
  defaultOpen = false,
  setCourse,
  handleDelete,
}: {
  type?: "landing" | "course";
  section?: SectionType;
  lesson: LessonType;
  defaultOpen?: boolean;
  index?: number;
  setCourse: any;
  handleDelete: any;
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
  };

  const handleChangeCourse = (e: any) => {
    const { name, value } = e;
    setCourse((prev: any) => {
      if (!prev) return prev;
      return {
        ...prev,
        sections: prev.sections.map((s: any) =>
          s.id === section?.id
            ? {
                ...s,
                lessons: s.lessons.map((l: any) =>
                  l.id === lesson.id ? { ...l, [name]: value } : l,
                ),
              }
            : s,
        ),
      };
    });
  };

  const handleChangeLanding = () => {};

  const courseFields = [
    {
      id: "lesson_name",
      label: "title",
      placeholder: "title.placeholder",
      inputType: "text",
    },
    {
      id: "video_link",
      label: "fullLink",
      placeholder: "fullLink.placeholder",
      inputType: "text",
    },
  ];

  const landingFields = [
    {
      id: "lesson_name",
      label: "title",
      placeholder: "title.placeholder",
      inputType: "text",
    },
    {
      id: "program_text",
      label: "programText",
      placeholder: "programText.placeholder",
      type: "textarea",
    },
    {
      id: "short_link",
      label: "shortLink",
      placeholder: "shortLink.placeholder",
      inputType: "text",
    },
    {
      id: "duration",
      label: "duration",
      placeholder: "duration.placeholder",
      inputType: "text",
    },
  ];

  return (
    <CollapsibleSection
      title="admin.lessons"
      data={{
        id: lesson.id,
        name: lesson.lesson_name,
        lesson_name: lesson.lesson_name,
        video_link: lesson.video_link,
      }}
      fields={type === "course" ? courseFields : landingFields}
      isOpen={isOpen}
      toggleOpen={toggleOpen}
      handleDelete={handleDelete}
      onChange={type === "course" ? handleChangeCourse : handleChangeLanding}
    />
  );
};

export default EditLesson;
