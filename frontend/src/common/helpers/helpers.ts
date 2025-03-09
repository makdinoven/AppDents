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

export const processProgramText = (text: string) => {
  const lines = text.split("\n").map((line) => line.trim());

  const regularLines: string[] = [];
  const bulletPointGroups: { text: string; points: string[] }[] = [];
  let currentGroup: { text: string; points: string[] } | null = null;

  lines.forEach((line) => {
    const trimmedLine = line.trim();

    if (trimmedLine.startsWith("-") || trimmedLine.startsWith("–")) {
      if (currentGroup) {
        bulletPointGroups.push(currentGroup);
      }
      currentGroup = {
        text: trimmedLine.substring(1).trim(),
        points: [],
      };
    } else if (trimmedLine.startsWith("•")) {
      if (currentGroup) {
        currentGroup.points.push(trimmedLine.substring(1).trim());
      }
    } else {
      if (currentGroup) {
        bulletPointGroups.push(currentGroup);
        currentGroup = null;
      }
      regularLines.push(trimmedLine);
    }
  });

  if (currentGroup) {
    bulletPointGroups.push(currentGroup);
  }

  return { regularLines, bulletPointGroups };
};

export const isValidUrl = (url: string) => {
  const regex =
    /^(https?:\/\/)?([a-zA-Z0-9]+[.-])*[a-zA-Z0-9]+(\.[a-zA-Z]{2,})?(:\d+)?(\/[^\s]*)?$/;
  return regex.test(url);
};

export const getPricesData = (landing: any) => ({
  old_price: landing?.old_price ? `$${landing?.old_price}` : "",
  new_price: landing?.new_price ? `$${landing?.new_price}` : "",
});

export const calculateDiscount = (oldPrice: number, newPrice: number) => {
  return Math.round(((oldPrice - newPrice) / oldPrice) * 100);
};

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
