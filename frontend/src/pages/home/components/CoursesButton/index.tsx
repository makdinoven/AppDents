import { FC } from 'react';
import { ActionIcon, Stack, Text } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';
import classes from './index.module.css';

interface CoursesButtonProps {}

const CoursesButton: FC<CoursesButtonProps> = () => (
  <ActionIcon
    pos="absolute"
    top={151}
    left={20}
    variant="transparent"
    size="lg"
    w={137}
    h={107}
    py={16}
    pl={12}
    pr={12}
    radius="md"
    onClick={undefined}
    c="background.3"
    bg="text.4"
    className={classes.actionIcon}
  >
    <Stack pos="relative">
      <Icon type={IconType.CircleArrow} size={27} color="inherit" />
      <Text size="lg" c="inherit">
        Online courses for dentists
      </Text>
    </Stack>
  </ActionIcon>
);

export default CoursesButton;
