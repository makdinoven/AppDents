import { useMutation, useQuery, UseQueryOptions } from '@tanstack/react-query';

import { apiService } from 'services';

import queryClient from 'query-client';

import { ApiError } from 'types';
import { User } from './account.types';

const BASE_URL = '/users';

export const useSignIn = <T>() =>
  useMutation<{ access_token: string; token_type: string }, ApiError, T>({
    mutationFn: (data: T) => apiService.post(`${BASE_URL}/login`, data),
    onSuccess: (data) => {
      localStorage.setItem('token', data.access_token);
    },
  });

export const useSignOut = () =>
  useMutation<void, ApiError>({
    mutationFn: () => Promise.resolve(),
    onSuccess: () => {
      queryClient.setQueryData(['account'], null);
      localStorage.clear();
    },
  });

export const useSignUp = <T>() => {
  interface SignUpResponse {
    signupToken: string;
  }

  return useMutation<SignUpResponse, ApiError, T>({
    mutationFn: (data: T) => apiService.post(`${BASE_URL}/register`, data),
  });
};

export const useForgotPassword = <T>() =>
  useMutation<void, ApiError, T>({
    mutationFn: (data: T) => apiService.post('/account/forgot-password', data),
  });

export const useResetPassword = <T>() =>
  useMutation<void, ApiError, T>({
    mutationFn: (data: T) => apiService.put('/account/reset-password', data),
  });

export const useResendEmail = <T>() =>
  useMutation<null, ApiError, T>({
    mutationFn: (data: T) => apiService.post('/account/resend-email', data),
  });

export const useGet = (options: Partial<UseQueryOptions<User>> = {}) =>
  useQuery<User>({
    queryKey: ['account'],
    queryFn: () => apiService.get(`${BASE_URL}/me`),
    staleTime: 5 * 1000,
    ...options,
  });

export const useUpdate = <T>() =>
  useMutation<User, ApiError, T>({
    mutationFn: (data: T) => apiService.put('/account', data),
  });

export const useUploadAvatar = <T>() =>
  useMutation<User, ApiError, T>({
    mutationFn: (data: T) => apiService.post('/account/avatar', data),
    onSuccess: (data) => {
      queryClient.setQueryData(['account'], data);
    },
  });

export const useRemoveAvatar = () =>
  useMutation<User, ApiError>({
    mutationFn: () => apiService.delete('/account/avatar'),
    onSuccess: (data) => {
      queryClient.setQueryData(['account'], data);
    },
  });
