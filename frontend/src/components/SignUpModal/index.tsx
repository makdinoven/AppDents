import { Button, Input, Stack, Title, Text } from '@mantine/core';

import { FC } from 'react';
import { useForm } from 'react-hook-form';
import { SCREEN } from 'components/AuthPopover';
import { accountApi } from 'resources/account';
import { zodResolver } from '@hookform/resolvers/zod';
import { signUpSchema } from 'resources/account/account.schemas';
import { z } from 'zod';

import { handleApiError } from 'utils';
import { showNotification } from '@mantine/notifications';
import classes from './index.module.css';

type SignUpParams = z.infer<typeof signUpSchema>;

type SignUpModalProps = {
  setScreen: (screen: SCREEN) => void;
};

const SignUpModal: FC<SignUpModalProps> = ({ setScreen }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ email: string; name: string }>({
    resolver: zodResolver(signUpSchema),
  });

  const { mutate: signUp, isPending: isSignUpPending } = accountApi.useSignUp<SignUpParams>();

  const onSubmit = (data: SignUpParams) =>
    signUp(data, {
      onSuccess: () => {
        setScreen(SCREEN.LOGIN);
        showNotification({ message: 'A password was sent to your e-mail' });
      },
      onError: (e) => handleApiError(e),
    });

  return (
    <Stack miw={246} gap={35} justify="center" align="center">
      <Stack gap={40} justify="center" align="center" w="100%">
        <Title order={2} c="background.3" w="fit-content">
          SIGN UP
        </Title>

        <form className={classes.form} onSubmit={handleSubmit(onSubmit)}>
          <Stack gap={20}>
            <Input {...register('email')} placeholder="Mail..." error={errors.email?.message} />

            <Input {...register('name')} placeholder="Name.." error={errors.name?.message} />
          </Stack>

          <Button variant="outline-light" type="submit" loading={false} fullWidth mt={32} disabled={isSignUpPending}>
            SIGN UP
          </Button>
        </form>
      </Stack>

      <Stack justify="center" align="center" gap={5}>
        <Text size="lg" c="background.3">
          Already have an account?
        </Text>

        <Button variant="transparent" w="fit-content" onClick={() => setScreen(SCREEN.LOGIN)}>
          <Text size="lg" c="background.3">
            LOG IN
          </Text>
        </Button>
      </Stack>
    </Stack>
  );
};
export default SignUpModal;
