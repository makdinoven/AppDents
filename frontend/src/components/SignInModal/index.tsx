import { Button, Group, Input, Stack, Title, Text } from '@mantine/core';

import { FC } from 'react';
import { useForm } from 'react-hook-form';

import { handleApiError } from 'utils';
import { ApiError } from 'types';
import { signInSchema } from 'resources/account/account.schemas';
import { accountApi } from 'resources/account';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/router';
import classes from './index.module.css';

type SignInModalProps = {
  setScreen: (screen: SCREEN) => void;
  onClose?: () => void;
};

enum SCREEN {
  LOGIN = 'login',
  SIGN_UP = 'sign-up',
  RESET_PASSWORD = 'reset-password',
}

type SignInParams = z.infer<typeof signInSchema>;

const SignInModal: FC<SignInModalProps> = ({ setScreen }) => {
  const router = useRouter();

  const {
    register,
    formState: { errors },
    handleSubmit,
  } = useForm<SignInParams>({
    resolver: zodResolver(signInSchema),
  });

  const { mutate: signIn, isPending: isSignInPending } = accountApi.useSignIn();

  const onSubmit = (data: unknown) =>
    signIn(data, {
      onError: (e: ApiError) => handleApiError(e),
      onSuccess: () => {
        router.reload();
      },
    });

  return (
    <Stack miw={246} gap={35} justify="center" align="center">
      <Stack gap={40} justify="center" align="center" w="100%">
        <Title order={2} c="background.3" w="fit-content">
          LOG IN
        </Title>

        <form className={classes.form} onSubmit={handleSubmit(onSubmit)}>
          <Stack gap={20}>
            <Input {...register('email')} placeholder="Mail..." error={errors.email?.message} />

            <Input
              {...register('password')}
              placeholder="Password..."
              type="password"
              error={errors.password?.message}
            />

            {/* {errors.credentials && (
                <Alert icon={<IconAlertCircle />} color="red">
                  {errors.credentials.message}
                </Alert>
              )} */}
          </Stack>

          <Stack align="flex-end" gap={14}>
            <Button variant="outline-light" type="submit" loading={isSignInPending} fullWidth mt={32}>
              LOG IN
            </Button>

            <Button
              variant="transparent"
              w="fit-content"
              onClick={() => {
                setScreen(SCREEN.RESET_PASSWORD);
              }}
            >
              <Text size="lg" c="background.3">
                Forgot password?
              </Text>
            </Button>
          </Stack>
        </form>
      </Stack>

      <Group justify="center" gap={5}>
        <Text size="lg" c="background.3">
          First time here?
        </Text>

        <Button
          variant="transparent"
          w="fit-content"
          onClick={() => {
            setScreen(SCREEN.SIGN_UP);
          }}
        >
          <Text size="lg" c="background.3">
            SIGN UP
          </Text>
        </Button>
      </Group>
    </Stack>
  );
};

export default SignInModal;
