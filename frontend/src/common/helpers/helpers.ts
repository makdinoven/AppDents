import { t } from "i18next";

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

export const formatAuthorsDesc = (authors: any) => {
  return authors?.length > 0
    ? `${t("landing.by")} ${
        authors
          ?.slice(0, 3)
          .map((author: any) => capitalizeText(author.name))
          .join(", ") + (authors.length > 3 ? ` ${t("etAl")}` : "")
      }`
    : null;
};

const getCookie = (name: any) => {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? match[2] : null;
};

export const getFacebookData = () => {
  const fbp = getCookie("_fbp") || "";
  const fbc = getCookie("_fbc") || "";
  return { fbp, fbc };
};

export const transformTags = (
  tags: { id: number; name: string }[],
): { id: number; name: string; value: string }[] => {
  const transformed = tags.map((tag) => ({
    ...tag,
    value: tag.name,
  }));

  return [{ id: 0, name: "tag.allCourses", value: "all" }, ...transformed];
};

export const scrollToElement = (triggerRef: any) => {
  triggerRef.current?.scrollIntoView({ behavior: "smooth" });
};

export const scrollToElementById = (id: string, offset = 100) => {
  const element = document.getElementById(id);
  if (element) {
    const topPosition =
      element.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({
      top: topPosition,
      behavior: "smooth",
    });
  }
};

export const keepFirstTwoWithInsert = (initialStr: string) => {
  const parts = initialStr.split(" ");
  if (parts.length < 2) return initialStr;
  const secondWord = parts[1].endsWith(":") ? parts[1].slice(0, -1) : parts[1];

  return `${parts[0]} ${t("landing.online")} ${secondWord}`;
};

export const getPricesData = (landing: any) => ({
  old_price: landing?.old_price ? `${landing?.old_price}` : "",
  new_price: landing?.new_price ? `${landing?.new_price}` : "",
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
