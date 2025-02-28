export interface ModuleType {
  id: number;
  title: string;
  duration: string;
  full_video_link: string;
  program_text: string;
  short_video_link: string;
}

export interface SectionType {
  id: number;
  name: string;
  modules: ModuleType[];
}

export interface LandingType {
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

export interface CourseType {
  name: string;
  description: string;
  landing: LandingType;
  sections: SectionType[];
}
