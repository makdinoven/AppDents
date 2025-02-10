import { Button, Stack, Text } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';
import Head from 'next/head';

import { useRouter } from 'next/router';
import { RoutePath } from 'routes';
import classes from './index.module.css';
import Header from './components/Header';

const testCourse = {
  id: 1,
  name: 'Fundamentals of Dentistry',
  description: 'A comprehensive course on essential dental knowledge and practices.',
  sections: [
    {
      id: 1,
      name: 'Introduction to Dentistry',
      modules: [
        {
          id: 1,
          title: 'Dental Anatomy',
          short_video_link: 'https://short.link/dental-anatomy',
          full_video_link: 'https://full.link/dental-anatomy',
          program_text: 'Overview of teeth structure and oral cavity anatomy.',
          duration: '15 minutes',
        },
        {
          id: 2,
          title: 'Oral Health and Hygiene',
          short_video_link: 'https://short.link/oral-hygiene',
          full_video_link: 'https://full.link/oral-hygiene',
          program_text: 'Best practices for maintaining oral health.',
          duration: '20 minutes',
        },
      ],
    },
    {
      id: 2,
      name: 'Clinical Procedures',
      modules: [
        {
          id: 3,
          title: 'Cavity Treatment',
          short_video_link: 'https://short.link/cavity-treatment',
          full_video_link: 'https://full.link/cavity-treatment',
          program_text: 'Steps involved in diagnosing and treating cavities.',
          duration: '25 minutes',
        },
      ],
    },
  ],
};

const Course = () => {
  const router = useRouter();

  return (
    <>
      <Head>
        <title>{testCourse.name}</title>
      </Head>

      <Stack className={classes.main}>
        <Button
          variant="transparent"
          onClick={() => router.push(RoutePath.Home)}
          leftSection={<Icon type={IconType.ChevronCompactLeft} size={35} />}
        >
          <Text size="xl" c="text.8">
            Back
          </Text>
        </Button>

        <Stack w="100%">
          <Header course={testCourse} />
        </Stack>
      </Stack>
    </>
  );
};

export default Course;
