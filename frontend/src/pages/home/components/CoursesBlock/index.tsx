import { FC } from 'react';
import { Divider, Grid, Group, Stack, Text } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import CoursePreview from './CoursePreview';

const courses = [{}, {}, {}, {}];

const changeOrder = (index: number) => {
  if (index === 2) {
    return 3;
  }
  if (index === 3) {
    return 2;
  }

  return index;
};

interface CourseBlockProps {}

const CourseList: FC<CourseBlockProps> = () => {
  const isMobile = useMediaQuery('(max-width: 400px)');

  return (
    <Stack gap={20}>
      <Group gap={10} justify="center">
        <Divider color="text.8" orientation="horizontal" w={20} />

        <Text c="main.3" size="xl">
          Our courses
        </Text>

        <Divider color="text.8" orientation="horizontal" flex={1} />
      </Group>

      <Grid columns={isMobile ? 1 : 2}>
        {courses.slice(0, isMobile ? 2 : 4).map((c, index) => (
          <Grid.Col span={1}>
            <CoursePreview index={changeOrder(index)} />
          </Grid.Col>
        ))}
      </Grid>
    </Stack>
  );
};

export default CourseList;
