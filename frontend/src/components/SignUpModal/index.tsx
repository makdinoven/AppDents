import { Button, Input, Stack, Title, Text } from '@mantine/core';

import Modal from 'components/Modal';
import { FC } from 'react';
import { useForm } from 'react-hook-form';

import SignInModal from 'components/SignInModal';
import { useDisclosure } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import modalClasses from 'components/Modal/index.module.css';
import { ModalId } from 'types';
import classes from './index.module.css';

// import { signInSchema } from 'schemas';
// import { SignInParams } from 'types';

// type SignInParamsWithCredentials = SignInParams & { credentials?: string };

type SignUpModalProps = {
  onClose: () => void;
};

const SignUpModal: FC<SignUpModalProps> = ({ onClose }) => {
  const { register } = useForm<{ email: string; name: string }>();

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

          <Button
            variant="transparent"
            w="fit-content"
            onClick={() => {
              modals.closeAll();
              modals.open({
                modalId: ModalId.SIGN_IN,
                children: <SignInModal onClose={() => modals.close(ModalId.SIGN_IN)} />,
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
              LOG IN
            </Text>
          </Button>
        </Stack>
      </Stack>
    </Modal>
  );
};
export default SignUpModal;
