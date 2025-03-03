export interface LessonType {
  id: number;
  lesson_name: string;
  video_link: string;
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
  title: string;
  old_price: number;
  price: number;
  main_image: string;
  main_text: string;
  language: string;
  tag_id: number;
  authors: [];
  sales_count: number;
}
