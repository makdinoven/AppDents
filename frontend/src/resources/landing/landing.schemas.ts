import { z } from 'zod';

export const signUpSchema = z.object({
  name: z.string().min(1, 'Please enter name').max(100),
  email: z.string().min(1, 'Please enter email').email('Email format is incorrect.'),
});

export const signInSchema = z.object({
  email: z.string().min(1, 'Please enter email').email('Email format is incorrect.'),
  password: z.string().min(1, 'Please enter password').max(100),
});
