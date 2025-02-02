import { useState } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { Anchor, Button, Group, Stack, Text, TextInput, Title } from '@mantine/core';
import { useForm } from 'react-hook-form';

import { accountApi } from 'resources/account';

import { RoutePath } from 'routes';

const ForgotPassword: NextPage = () => {
  const [email] = useState('');

  const { isPending: isForgotPasswordPending } = accountApi.useForgotPassword();

  const { register } = useForm();

  // const onSubmit = (data: unknown) =>
  //   forgotPassword(data, {
  //     onSuccess: () => setEmail(data.email),
  //     onError: (e) => handleApiError(e, setError),
  //   });

  if (email) {
    return (
      <>
        <Head>
          <title>Forgot password</title>
        </Head>
        <Stack w={328}>
          <Title order={2}>Reset link has been sent</Title>

          <Text>
            A link to reset your password has just been sent to{' '}
            <Text fw={600} span>
              {email}
            </Text>
            . Please check your email inbox and follow the directions to reset your password.
          </Text>

          <Button>Back to Sign In</Button>
        </Stack>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Forgot password</title>
      </Head>

      <Stack w={400} fz={18} gap={24}>
        <Title order={1}>Forgot Password</Title>

        <Text m={0}>Please enter your email and we&apos;ll send a link to reset your password.</Text>

        <form>
          <Stack gap={34}>
            <TextInput
              {...register('email')}
              type="email"
              label="Email address"
              placeholder="Enter your email address"
              // error={errors.email?.message}
            />

            <Button type="submit" loading={isForgotPasswordPending}>
              Send reset link
            </Button>
          </Stack>
        </form>

        <Group justify="center">
          Have an account?
          <Anchor component={Link} href={RoutePath.Home}>
            Sign in
          </Anchor>
        </Group>
      </Stack>
    </>
  );
};

export default ForgotPassword;
