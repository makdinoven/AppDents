import { Button, Group, Input, Stack, Title, Text } from '@mantine/core';

import Modal from 'components/Modal';
import { FC } from 'react';
import { useForm } from 'react-hook-form';

import classes from './index.module.css';

// import { signInSchema } from 'schemas';
// import { SignInParams } from 'types';

// type SignInParamsWithCredentials = SignInParams & { credentials?: string };

type SignInModalProps = {
  opened: boolean;
  onClose: () => void;
};

const SignInModal: FC<SignInModalProps> = ({ onClose, opened }) => {
  const { register } = useForm<{ email: string; password: string }>();

  // const { mutate: signIn, isPending: isSignInPending } = accountApi.useSignIn();

  // const onSubmit = (data: unknown) =>
  //   signIn(data, {
  //     onError: (e) => handleApiError(e, setError),
  //   });

  return (
    <Modal onClose={onClose} opened={opened}>
      <Stack miw={246} gap={35} justify="center" align="center">
        <Stack gap={40} justify="center" align="center" w="100%">
          <Title order={2} c="background.3" w="fit-content">
            LOG IN
          </Title>

          <form className={classes.form}>
            <Stack gap={20}>
              <Input
                {...register('email')}
                placeholder="Mail..."
                // error={errors.email?.message}
              />

              <Input
                {...register('password')}
                placeholder="Password..."
                type="password"
                // error={errors.password?.message}
              />

              {/* {errors.credentials && (
                <Alert icon={<IconAlertCircle />} color="red">
                  {errors.credentials.message}
                </Alert>
              )} */}
            </Stack>

            <Stack align="flex-end" gap={14}>
              <Button variant="outline-light" type="submit" loading={false} fullWidth mt={32}>
                LOG IN
              </Button>

              <Button variant="transparent" w="fit-content">
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

          <Button variant="transparent" w="fit-content">
            <Text size="lg" c="background.3">
              SIGN UP
            </Text>
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
};
export default SignInModal;
