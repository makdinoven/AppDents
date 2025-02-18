import { useQuery, UseQueryOptions } from '@tanstack/react-query';

import { apiService } from 'services';

import { Author } from './author.types';

const BASE_URL = '/authors';

export const useList = (options: Partial<UseQueryOptions<Author[]>> = {}) =>
  useQuery<Author[]>({
    queryKey: ['authors'],
    queryFn: () => apiService.get(BASE_URL),
    ...options,
  });

export const useGet = (id: string, options: Partial<UseQueryOptions<Author>> = {}) =>
  useQuery<Author>({
    queryKey: ['authors', id],
    queryFn: () => apiService.get(`${BASE_URL}/${id}`),
    ...options,
  });
