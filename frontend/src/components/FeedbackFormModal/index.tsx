import { Button, Input, Stack, Title } from '@mantine/core';

import Modal from 'components/Modal';
import { FC } from 'react';
import { useForm } from 'react-hook-form';

import classes from './index.module.css';

// import { signInSchema } from 'schemas';
// import { SignInParams } from 'types';

// type SignInParamsWithCredentials = SignInParams & { credentials?: string };

type FeedbackFormModalProps = {
  onClose: () => void;
};

const FeedbackFormModal: FC<FeedbackFormModalProps> = ({ onClose }) => {
  const { register } = useForm<{ email: string; subject: string; lecturerName: string }>();

  return (
    <Modal onClose={onClose}>
      <Stack gap={40} justify="center" align="center" w="100%" miw={246}>
        <Title order={2} c="background.3" w="fit-content">
          FEEDBACK FORM
        </Title>

        <form className={classes.form}>
          <Stack gap={20}>
            <Input
              {...register('email')}
              placeholder="Mail..."
              // error={errors.email?.message}
            />

            <Input
              {...register('subject')}
              placeholder="Subject..."
              // error={errors.email?.message}
            />

            <Input
              {...register('lecturerName')}
              placeholder="Lecturer..."
              // error={errors.email?.message}
            />
          </Stack>

          <Button variant="outline-light" type="submit" loading={false} fullWidth mt={32}>
            SUBMIT
          </Button>
        </form>
      </Stack>
    </Modal>
  );
};
export default FeedbackFormModal;
