import { Box, Button, Group, Stack, Text } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';

import Icon, { IconType } from 'components/Icon';

import { useRouter } from 'next/router';
import { RoutePath } from 'routes';
import classes from './index.module.css';

const greenStyleSettings = {
  textColor: 'text.8',
  backgroundColor: 'main.3',
};

const blueStyleSettings = {
  textColor: 'secondaryBlue.5',
  backgroundColor: 'secondarySkyBlue.4',
};

const getPreviewStyle = (index: number) => (index % 2 === 0 ? greenStyleSettings : blueStyleSettings);

type CoursePreviewProps = {
  index: number;
  course: {
    name: string;
    description: string;
  };
};

const CoursePreview = ({ index, course }: CoursePreviewProps) => {
  const isMobile = useMediaQuery('(max-width: 400px)');
  const router = useRouter();

  const styles = getPreviewStyle(index);

  return (
    <Box w="100%" maw="100%" mih={isMobile ? 80 : 110} bg={styles.backgroundColor} className={classes.main}>
      <Group gap={20} wrap={isMobile ? 'wrap' : 'nowrap'} align="flex-end">
        <Stack w="90%" align="flex-start" gap={5}>
          <Text size="xl" c={styles.textColor}>
            {course.name}
          </Text>

          <Text size="md">{course.name}</Text>
        </Stack>

        <Button
          variant="outline-bottom"
          h={24}
          rightSection={<Icon type={IconType.Arrow} color="inherit" size={20} />}
          onClick={() => router.push(`${RoutePath.Courses}/new`)}
        >
          View course
        </Button>
      </Group>
    </Box>
  );
};

export default CoursePreview;
