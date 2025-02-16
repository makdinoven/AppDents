import { Box, Divider, Group, Stack, Title, Text, Image } from '@mantine/core';
import { ColoredPaper, Icon } from 'components';
import { IconType } from 'components/Icon';

import classes from './index.module.css';
import PurchaseButton from '../PurchaseButton';

type HeaderProps = {
  course: {
    name: string;
    description: string;
  };
};

const Header = ({ course }: HeaderProps) => (
  <Group w="100%" wrap="nowrap" justify="start" align="start" gap={20}>
    <Box w="50%" h="582px">
      <ColoredPaper
        rightTopOffset={{ w: 325, h: 120 }}
        leftBottomOffset={{ w: 190, h: 208 }}
        childrenClassName={classes.childrenClassName}
      >
        <Image src="/images/course-image.png" alt="Demo" radius={20} width="100%" h={324} />
      </ColoredPaper>
    </Box>

    <Stack w="50%" justify="space-between" h="582px">
      <Stack w="100%" pos="relative" gap={20}>
        <Title order={1} c="text.8" tt="uppercase" pos="relative" textWrap="nowrap" right="50%">
          online course
        </Title>

        <Divider color="text.8" orientation="horizontal" w="100%" h={1} />

        <Title order={2} c="main.3" tt="uppercase">
          {course.name}
        </Title>

        <Group gap={0} align="center" w="80%" flex={1} wrap="nowrap" miw={160}>
          <Divider color="text.8" orientation="horizontal" h={2} w="50%" maw={600} />
          <Icon type={IconType.CircleArrowThin} size={66} color="green" />
        </Group>

        <Text size="lg" c="text.8">
          {course.description}
        </Text>
      </Stack>

      <PurchaseButton />
    </Stack>
  </Group>
);

export default Header;
