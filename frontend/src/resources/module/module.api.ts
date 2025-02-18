import { useQuery, UseQueryOptions } from '@tanstack/react-query';

import { apiService } from 'services';

import { Module } from './module.types';

const BASE_URL = '/modules';

export const useList = (options: Partial<UseQueryOptions<Module[]>> = {}) =>
  useQuery<Module[]>({
    queryKey: ['modules'],
    queryFn: () => apiService.get(BASE_URL),
    ...options,
  });

export const useGet = (id: string, options: Partial<UseQueryOptions<Module>> = {}) =>
  useQuery<Module>({
    queryKey: ['modules', id],
    queryFn: () => apiService.get(`${BASE_URL}/${id}`),
    ...options,
  });
