import { useQuery, UseQueryOptions } from '@tanstack/react-query';

import { apiService } from 'services';

import { Landing, LandingLanguage } from './landing.types';

const BASE_URL = '/landings';

export const useList = (options: Partial<UseQueryOptions<Landing[]>> = {}) =>
  useQuery<Landing[]>({
    queryKey: ['landings'],
    queryFn: () => apiService.get(BASE_URL),
    ...options,
  });

const landingPages: Landing[] = [
  {
    id: '2',
    language: LandingLanguage.EN,
    course_id: 102,
    title: 'Damon 2.0: How to Treat All Common Malocclusions',
    tag: 'Orthodontics',
    main_image: 'https://example.com/damon2.0-main.jpg',
    duration: '6 weeks',
    old_price: 299,
    price: 249,
    main_text: 'Learn how to effectively treat various malocclusions using the Damon 2.0 self-ligating system.',
    slug: 'damon-2-malocclusions',
    course: {
      id: 102,
      name: 'Damon 2.0 Orthodontic Treatment',
      description: 'A specialized course covering the treatment of malocclusions using Damon 2.0 technology.',
    },
    authors: [
      { id: 'a3', name: 'Dr. Emily Carter' },
      { id: 'a4', name: 'Dr. Michael Lee' },
    ],
    modules: [
      {
        id: 1,
        title: 'Introduction to Damon 2.0',
        short_video_link: 'https://example.com/damon-intro-short.mp4',
        full_video_link: 'https://example.com/damon-intro-full.mp4',
        program_text: 'Overview of the Damon 2.0 system and its benefits.',
        duration: '45 minutes',
      },
      {
        id: 2,
        title: 'Treating Crowding with Damon 2.0',
        short_video_link: 'https://example.com/crowding-short.mp4',
        full_video_link: 'https://example.com/crowding-full.mp4',
        program_text: 'Step-by-step approach to resolving dental crowding.',
        duration: '1 hour',
      },
      {
        id: 3,
        title: 'Correcting Overbite and Underbite',
        short_video_link: 'https://example.com/bite-correction-short.mp4',
        full_video_link: 'https://example.com/bite-correction-full.mp4',
        program_text: 'Techniques for treating deep bite and underbite with Damon 2.0.',
        duration: '1.5 hours',
      },
    ],
  },
  {
    id: '5',
    language: LandingLanguage.EN,
    course_id: 105,
    title: 'Advanced Orthodontics with Damon 2.0',
    tag: 'Orthodontics',
    main_image: 'https://example.com/damon-advanced.jpg',
    duration: '10 weeks',
    old_price: 399,
    price: 349,
    main_text: 'Master advanced orthodontic techniques using Damon 2.0 for complex cases.',
    slug: 'advanced-damon-2',
    course: {
      id: 105,
      name: 'Advanced Damon 2.0 Techniques',
      description: 'In-depth training on treating complex orthodontic cases with Damon 2.0.',
    },
    authors: [{ id: 'a9', name: 'Dr. Sarah Thompson' }],
    modules: [
      {
        id: 1,
        title: 'Case Studies in Advanced Damon 2.0',
        short_video_link: 'https://example.com/advanced-cases-short.mp4',
        full_video_link: 'https://example.com/advanced-cases-full.mp4',
        program_text: 'Analyzing difficult cases and their treatment plans.',
        duration: '1 hour',
      },
      {
        id: 2,
        title: 'Biomechanics of Self-Ligating Brackets',
        short_video_link: 'https://example.com/biomechanics-short.mp4',
        full_video_link: 'https://example.com/biomechanics-full.mp4',
        program_text: 'Understanding force distribution and movement control.',
        duration: '1.5 hours',
      },
    ],
  },
  {
    id: '6',
    language: LandingLanguage.EN,
    course_id: 106,
    title: 'Damon 2.0 for Beginners: A Step-by-Step Guide',
    tag: 'Orthodontics',
    main_image: 'https://example.com/damon-beginners.jpg',
    duration: '4 weeks',
    old_price: 199,
    price: 149,
    main_text: 'A comprehensive guide for beginners looking to master Damon 2.0 techniques.',
    slug: 'damon-2-beginners',
    course: {
      id: 106,
      name: "Beginner's Guide to Damon 2.0",
      description: 'Step-by-step training for new orthodontists using Damon 2.0.',
    },
    authors: [
      { id: 'a10', name: 'Dr. Mark Reynolds' },
      { id: 'a11', name: 'Dr. Sophia Kim' },
    ],
    modules: [
      {
        id: 1,
        title: 'Getting Started with Damon 2.0',
        short_video_link: 'https://example.com/getting-started-short.mp4',
        full_video_link: 'https://example.com/getting-started-full.mp4',
        program_text: 'Introduction to the Damon system for new users.',
        duration: '30 minutes',
      },
      {
        id: 2,
        title: 'Basic Adjustments and Maintenance',
        short_video_link: 'https://example.com/basic-adjustments-short.mp4',
        full_video_link: 'https://example.com/basic-adjustments-full.mp4',
        program_text: 'How to make initial adjustments and maintain Damon braces.',
        duration: '45 minutes',
      },
      {
        id: 3,
        title: 'Early Troubleshooting and Common Mistakes',
        short_video_link: 'https://example.com/troubleshooting-short.mp4',
        full_video_link: 'https://example.com/troubleshooting-full.mp4',
        program_text: 'Identifying and resolving common beginner errors.',
        duration: '1 hour',
      },
    ],
  },
];

export const useGet = (id: string, options: Partial<UseQueryOptions<Landing>> = {}) =>
  useQuery<Landing>({
    queryKey: ['landings', id],
    queryFn: () => Promise.resolve(landingPages.find((l) => l.id === id) || landingPages[0]),
    // queryFn: () => apiService.get(`${BASE_URL}/${id}`),
    ...options,
  });
