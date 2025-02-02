import { FC } from 'react';
import { Divider, Group, Stack, Text } from '@mantine/core';
import CoursePreview from './CoursePreview';

const courses = [{}, {}];

interface CourseBlockProps {}

const CourseList: FC<CourseBlockProps> = () => (
  // const [search, setSearch] = useInputState('');

  <Stack gap={20}>
    <Group gap={10} justify="center">
      <Divider color="text.8" orientation="horizontal" w={20} />

      <Text c="main.3" size="xl">
        Our courses
      </Text>

      <Divider color="text.8" orientation="horizontal" flex={1} />
    </Group>

    <Stack gap={0}>
      {courses.map((c, index) => (
        <CoursePreview index={index} />
      ))}
    </Stack>
  </Stack>
);
export default CourseList;
