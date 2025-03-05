export interface LessonType {
  id: number;
  name: string;
  link: string;
  lecturer: string;
  duration: string;
  program: string;
}

export interface SectionType {
  id: number;
  section_name: string;
  lessons: LessonType[];
}

export interface CourseType {
  name: string;
  description: string;
  sections: SectionType[];
}

export interface LandingType {
  id: number;
  landing_name: string;
  page_name: string;
  old_price: number;
  new_price: number;
  course_program: string;
  language: string;
  tag_id: number;
  sales_count: number;
  preview_photo: string;
  course_ids: [];
  author_ids: [];
  lessons_info: LessonType[];
}

export interface LandingFromListType {
  id: number;
  landing_name: string;
}
