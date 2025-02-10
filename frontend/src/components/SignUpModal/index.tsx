import { Button, Input, Stack, Title, Text } from '@mantine/core';

import { FC } from 'react';
import { useForm } from 'react-hook-form';
import { SCREEN } from 'components/AuthPopover';
import classes from './index.module.css';

// import { signInSchema } from 'schemas';
// import { SignInParams } from 'types';

// type SignInParamsWithCredentials = SignInParams & { credentials?: string };

type SignUpModalProps = {
  setScreen: (screen: SCREEN) => void;
};

const SignUpModal: FC<SignUpModalProps> = ({ setScreen }) => {
  const { register } = useForm<{ email: string; name: string }>();

  // const { mutate: signIn, isPending: isSignInPending } = accountApi.useSignIn();

  // const onSubmit = (data: unknown) =>
  //   signIn(data, {
  //     onError: (e) => handleApiError(e, setError),
  //   });

  return (
    <Stack miw={246} gap={35} justify="center" align="center">
      <Stack gap={40} justify="center" align="center" w="100%">
        <Title order={2} c="background.3" w="fit-content">
          SIGN UP
        </Title>

        <form className={classes.form}>
          <Stack gap={20}>
            <Input
              {...register('email')}
              placeholder="Mail..."
              // error={errors.email?.message}
            />

            <Input
              {...register('name')}
              placeholder="Name.."
              // error={errors.password?.message}
            />
          </Stack>

          <Button variant="outline-light" type="submit" loading={false} fullWidth mt={32}>
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
