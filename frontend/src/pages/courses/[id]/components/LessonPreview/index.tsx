import { Group, Stack, Title, Text, Divider, Box } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';

import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { Landing } from 'resources/landing/landing.types';
import { Module } from 'resources/module/module.types';
import classes from './index.module.css';
import PurchaseButton from '../PurchaseButton';

const ListItem = ({ text }: { text: string }) => (
  <Group wrap="nowrap">
    <Icon type={IconType.CircleArrowThin} color="green" size={30} />

    <Text>{text}</Text>
  </Group>
);

type LessonPreviewProps = {
  module: Module;
  landing: Pick<Landing, 'old_price' | 'price' | 'course'>;
};

const LessonPreview = ({ module, landing }: LessonPreviewProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <Stack>
      <Title order={2} c="main.3" tt="uppercase">
        {module.title}
      </Title>

      <Divider color="text.8" maw="60%" />

      <Group w="100%" align="flex-start" gap={20} wrap={isMobile ? 'wrap' : 'nowrap'}>
        <Stack>
          {[module.program_text].map((text) => (
            <ListItem text={text || ''} />
          ))}
        </Stack>

        <Stack>
          <Box className={classes.videoBox}>
            <iframe
              width={isMobile ? '100%' : '600'}
              height={isMobile ? '175' : '316'}
              src={module.short_video_link}
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
            Duration of the lesson: {module.duration}
          </Text>

          <PurchaseButton landing={landing} />
        </Stack>
      </Group>
    </Stack>
  );
};

export default LessonPreview;
