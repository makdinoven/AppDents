import { SectionType } from "../../types.ts";
import { useState } from "react";
import CollapsibleSection from "../common/CollapsibleSection/CollapsibleSection.tsx";

const EditLesson = ({
  type = "course",
  section,
  lesson,
  setCourse,
  handleDelete,
  moveLessonUp,
  moveLessonDown,
}: {
  type?: "landing" | "course";
  section?: SectionType;
  lesson: any;
  index?: number;
  setCourse: any;
  handleDelete: any;
  moveLessonUp: () => void;
  moveLessonDown: () => void;
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
  };

  const handleChangeCourse = (e: any) => {
    let { name, value } = e;
    if (name === "video_link") {
      value = handleShortenLink(value);
    }
    setCourse((prev: any) => {
      if (!prev) return prev;
      return {
        ...prev,
        sections: prev.sections.map((s: any) =>
          s.id === section?.id
            ? {
                ...s,
                lessons: s.lessons.map((l: any) =>
                  l.id === lesson.id ? { ...l, [name]: value } : l
                ),
              }
            : s
        ),
      };
    });
  };

  const handleChangeLanding = (e: any) => {
    let { name, value } = e;
    if (name === "link") {
      value = handleShortenLink(value);
    }
    setCourse((prev: any) => {
      if (!prev) return prev;
      return {
        ...prev,
        lessons_info: prev.lessons_info.map((l: any) =>
          l.id === lesson.id ? { ...l, [name]: value } : l
        ),
      };
    });
  };

  const handleShortenLink = (link: string) => {
    return link.replace(
      /^https:\/\/[^\/]+\.s3\.twcstorage\.ru(\/\S*)$/,
      "https://cdn.dent-s.com$1"
    );
  };

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
      id: "name",
      label: "title",
      placeholder: "title.placeholder",
      inputType: "text",
    },
    {
      id: "program",
      label: "programText",
      placeholder: "programText.placeholder",
      type: "textarea",
    },
    {
      id: "link",
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
    {
      id: "lecturer",
      label: "lecturer",
      placeholder: "lecturer.placeholder",
      inputType: "text",
    },
  ];

  return (
    <CollapsibleSection
      title="admin.lessons"
      handleMoveToTop={moveLessonUp}
      handleMoveToBottom={moveLessonDown}
      data={
        type === "course"
          ? {
              id: lesson.id,
              name: lesson.lesson_name,
              lesson_name: lesson.lesson_name,
              video_link: lesson.video_link,
            }
          : {
              id: lesson.id,
              name: lesson.name,
              link: lesson.link,
              duration: lesson.duration,
              lecturer: lesson.lecturer,
              program: lesson.program,
            }
      }
      fields={type === "course" ? courseFields : landingFields}
      isOpen={isOpen}
      toggleOpen={toggleOpen}
      handleDelete={handleDelete}
      onChange={type === "course" ? handleChangeCourse : handleChangeLanding}
    />
  );
};

export default EditLesson;
