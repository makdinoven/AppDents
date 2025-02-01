import Head from 'next/head';
import { Button, Input, Stack, Title, Text } from '@mantine/core';

import { RoutePath } from 'routes';
import Modal from 'components/Modal';
import { FC, useState } from 'react';
import { useForm } from 'react-hook-form';

import { useRouter } from 'next/router';
import classes from './index.module.css';

// import { signInSchema } from 'schemas';
// import { SignInParams } from 'types';

// type SignInParamsWithCredentials = SignInParams & { credentials?: string };

type ResetPasswordModalProps = {
  opened: boolean;
  onClose: () => void;
};

const ResetPasswordModal: FC<ResetPasswordModalProps> = ({ onClose, opened }) => {
  const [isSubmitted] = useState(false);
  const router = useRouter();

  // const { token } = router.query;

  const { register } = useForm<{ email: string; password: string }>();

  // const onSubmit = (data: ResetPasswordParams) => {
  //   if (typeof token !== 'string') return;

  //   resetPassword(
  //     {
  //       ...data,
  //       token,
  //     },
  //     {
  //       onSuccess: () => setSubmitted(true),
  //       onError: (e) => handleApiError(e),
  //     },
  //   );
  // };

  // if (!token) {
  //   return (
  //     <Stack w={328} gap="xs">
  //       <Title order={2} mb={0}>
  //         Invalid token
  //       </Title>

  //       <Text m={0}>Sorry, your token is invalid.</Text>
  //     </Stack>
  //   );
  // }

  if (isSubmitted) {
    return (
      <>
        <Head>
          <title>Reset Password</title>
        </Head>

        <Stack w={328}>
          <Title order={2}>Password has been updated</Title>

          <Text mt={0}>Your password has been updated successfully. You can now use your new password to sign in.</Text>

          <Button onClick={() => router.push(RoutePath.Home)}>Back to Sign In</Button>
        </Stack>
      </>
    );
  }

  return (
    <Modal onClose={onClose} opened={opened}>
      <Stack miw={246} gap={35} justify="center" align="center">
        <Stack gap={40} justify="center" align="center" w="100%">
          <Title order={2} c="background.3" w="fit-content">
            PASSWORD RESET
          </Title>

          <form className={classes.form}>
            <Input
              {...register('email')}
              placeholder="Mail..."
              // error={errors.email?.message}
            />

            <Button variant="outline-light" type="submit" loading={false} fullWidth mt={32}>
              RESET
            </Button>
          </form>
        </Stack>

        <Text size="lg" c="background.3" w="70%">
          A new password will be sent to your e-mail
        </Text>
      </Stack>
    </Modal>
  );
};
export default ResetPasswordModal;
