import { Button, Input, Stack, Title } from '@mantine/core';

import { FC } from 'react';
import { useForm } from 'react-hook-form';
import { Course } from 'resources/course/course.types';
import classes from './index.module.css';

type PurchaseModalProps = {
  course: Course;
};

const PurchaseModal: FC<PurchaseModalProps> = ({ course }) => {
  const {
    register,
    formState: { errors },
    handleSubmit,
  } = useForm({});

  const onSubmit = () => {};

  return (
    <Stack miw={246} gap={35} justify="center" align="center" pb={129}>
      <Stack gap={40} justify="center" align="center" w="100%">
        <Title order={2} c="background.3" w="fit-content" tt="uppercase">
          buy: {course.name}
        </Title>

        <form className={classes.form} onSubmit={handleSubmit(onSubmit)}>
          <Input
            {...register('email')}
            placeholder="Mail (to get to course)..."
            error={errors.email?.message as string}
          />

          <Button variant="outline-light" type="submit" fullWidth mt={32}>
            <Title order={3} tt="uppercase">
              pay
            </Title>
          </Button>
        </form>
      </Stack>
    </Stack>
  );
};

export default PurchaseModal;
