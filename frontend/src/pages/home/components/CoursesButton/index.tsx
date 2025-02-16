import { FC } from 'react';
import { ActionIcon, Stack, Text } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';
import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import classes from './index.module.css';

interface CoursesButtonProps {}

const CoursesButton: FC<CoursesButtonProps> = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <ActionIcon pos="absolute" variant="transparent" size="lg" onClick={undefined} className={classes.actionIcon}>
      <Stack pos="relative">
        <Icon type={IconType.CircleArrow} size={isMobile ? 27 : 92} color="inherit" />
        <Text size="lg" c="inherit">
          Online courses for dentists
        </Text>
      </Stack>
    </ActionIcon>
  );
};

export default CoursesButton;
