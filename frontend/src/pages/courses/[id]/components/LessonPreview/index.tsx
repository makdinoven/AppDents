import { Group, Stack, Title, Text, Divider, Box } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';

import classes from './index.module.css';
import PurchaseButton from '../PurchaseButton';

const ListItem = ({ text }: { text: string }) => (
  <Group>
    <Icon type={IconType.CircleArrowThin} color="green" size={30} />

    <Text>{text}</Text>
  </Group>
);

type LessonPreviewProps = {
  title: string;
  info: string[];
  duration: string;
};

const LessonPreview = ({ title, info, duration }: LessonPreviewProps) => (
  <Stack>
    <Title order={2} c="main.3" tt="uppercase">
      {title}
    </Title>

    <Divider color="text.8" maw="60%" />

    <Group w="100%" align="flex-start" gap={20}>
      <Stack>
        {info.map((text) => (
          <ListItem text={text} />
        ))}
      </Stack>

      <Stack>
        <Box className={classes.videoBox}>
          <iframe
            width="600"
            height="316"
            src=""
            title="YouTube video player"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerPolicy="strict-origin-when-cross-origin"
            allowFullScreen
          />
        </Box>

        <Text size="md" c="text.8" fs="italic">
          Here you can watch a{' '}
          <Text c="main.3" component="span">
            five-minute fragment
          </Text>{' '}
          of the lesson
        </Text>

        <Divider color="text.8" maw="100%" />

        <Text size="md" c="text.8" fs="italic">
          Duration of the lesson: {duration}
        </Text>

        <PurchaseButton />
      </Stack>
    </Group>
  </Stack>
);

export default LessonPreview;
