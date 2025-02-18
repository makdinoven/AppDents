import { Author } from 'resources/author/author.types';
import { Course } from 'resources/course/course.types';
import { Module } from 'resources/module/module.types';

export enum LandingLanguage {
  EN = 'en',
  ES = 'es',
  RU = 'ru',
}

export type Landing = {
  id: string;
  language: LandingLanguage;
  course_id: number;
  title: string;
  tag: string;
  main_image: string;
  duration: string;
  old_price: number;
  price: number;
  main_text: string;
  slug: string;
  course: Course;
  authors: Author[];
  modules: Module[];
};
