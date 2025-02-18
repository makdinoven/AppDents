import { useQuery, UseQueryOptions } from '@tanstack/react-query';

import { apiService } from 'services';

import { Course } from './course.types';

const BASE_URL = '/courses';

export const useList = (options: Partial<UseQueryOptions<Course[]>> = {}) =>
  useQuery<Course[]>({
    queryKey: ['course'],
    queryFn: () => apiService.get(BASE_URL),
    ...options,
  });

export const useGet = (id: string, options: Partial<UseQueryOptions<Course>> = {}) =>
  useQuery<Course>({
    queryKey: ['courses', id],
    queryFn: () => apiService.get(`${BASE_URL}/${id}`),
    ...options,
  });
