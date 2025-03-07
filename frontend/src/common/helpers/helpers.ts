export const getAuthHeaders = () => {
  const accessToken = localStorage.getItem("access_token");

  if (!accessToken) {
    throw new Error("No access token found");
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
};

export const generateId = () => Math.floor(Math.random() * 100000);

export const capitalizeText = (text: string) => {
  return text
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
};

export const normalizeCourse = (course: any) => {
  return {
    ...course,
    sections: course.sections.map((sectionObj: any) => {
      const sectionId = Object.keys(sectionObj)[0];
      return {
        id: Number(sectionId),
        section_name: sectionObj[sectionId].section_name,
        lessons: sectionObj[sectionId].lessons.map(
          (lesson: any, index: number) => ({
            id: index + 1,
            lesson_name: lesson.lesson_name,
            video_link: lesson.video_link,
          }),
        ),
      };
    }),
  };
};

export const denormalizeCourse = (course: any) => {
  return {
    ...course,
    sections: course.sections.map((section: any) => ({
      [section.id]: {
        section_name: section.section_name,
        lessons: section.lessons.map((lesson: any) => {
          const { id, ...rest } = lesson;
          return rest;
        }),
      },
    })),
  };
};

export const normalizeLessons = (lessons: any[]): any[] => {
  return lessons.map((lessonObj, index) => {
    const key = Object.keys(lessonObj)[0];
    const lesson = lessonObj[key];

    return {
      id: index + 1,
      program: lesson.program || "",
      link: lesson.link || "",
      duration: lesson.duration || "",
      name: lesson.name || "",
      lecturer: lesson.lecturer || "",
    };
  });
};

export const denormalizeLessons = (lessons: any) => {
  return lessons.map((lesson: any, index: number) => {
    return {
      [`lesson${index + 1}`]: {
        link: lesson.link || "",
        name: lesson.name || "",
        program: lesson.program || "",
        duration: lesson.duration || "",
        lecturer: lesson.lecturer || "",
      },
    };
  });
};
