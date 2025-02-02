import { Button, Group, Input, Stack, Title, Text } from '@mantine/core';

import Modal from 'components/Modal';
import { FC } from 'react';
import { useForm } from 'react-hook-form';

import { useDisclosure } from '@mantine/hooks';
import SignUpModal from 'components/SignUpModal';
import modalClasses from 'components/Modal/index.module.css';
import { modals } from '@mantine/modals';
import { ModalId } from 'types';
import classes from './index.module.css';
import ResetPasswordModal from 'components/ResetPasswordModal';

// import { signInSchema } from 'schemas';
// import { SignInParams } from 'types';

// type SignInParamsWithCredentials = SignInParams & { credentials?: string };

type SignInModalProps = {
  onClose: () => void;
};

const SignInModal: FC<SignInModalProps> = ({ onClose }) => {
  const { register } = useForm<{ email: string; password: string }>();

  // const { mutate: signIn, isPending: isSignInPending } = accountApi.useSignIn();

  // const onSubmit = (data: unknown) =>
  //   signIn(data, {
  //     onError: (e) => handleApiError(e, setError),
  //   });

  return (
    <Modal onClose={onClose}>
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

              <Button
                variant="transparent"
                w="fit-content"
                onClick={() => {
                  modals.closeAll();
                  modals.open({
                    modalId: ModalId.RESET_PASSWORD,
                    children: <ResetPasswordModal onClose={() => modals.close(ModalId.RESET_PASSWORD)} />,
                    size: 'xl',
                    withCloseButton: false,
                    classNames: {
                      header: modalClasses.header,
                      content: modalClasses.content,
                      body: modalClasses.body,
                      root: modalClasses.root,
                    },
                    yOffset: 41,
                    overlayProps: {
                      backgroundOpacity: 0.55,
                      blur: 3,
                    },
                  });
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
              modals.closeAll();
              modals.open({
                modalId: ModalId.SIGN_UP,
                children: <SignUpModal onClose={() => modals.close(ModalId.SIGN_UP)} />,
                size: 'xl',
                withCloseButton: false,
                classNames: {
                  header: modalClasses.header,
                  content: modalClasses.content,
                  body: modalClasses.body,
                  root: modalClasses.root,
                },
                yOffset: 41,
                overlayProps: {
                  backgroundOpacity: 0.55,
                  blur: 3,
                },
              });
            }}
          >
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
