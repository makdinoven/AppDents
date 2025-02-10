import { Button, Divider, Group, Stack, Text, Title } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';
import Head from 'next/head';

import { useRouter } from 'next/router';
import { RoutePath } from 'routes';
import { useMediaQuery } from '@mantine/hooks';
import { accountApi } from 'resources/account';
import { CoursePreview } from 'components';
import classes from './index.module.css';

const testCourse = {
  id: 1,
  name: 'Damon 2.0 How to treat all common malocclusions',
  description: 'By Bill Dischinger, Alfredo Rizzo, Trevor Nichols et. al.',
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

const Profile = () => {
  const isMobile = useMediaQuery('(max-width: 400px)');
  const router = useRouter();

  const { data: account } = accountApi.useGet();
  const { mutate: signOut, isPending: isSignOutPending } = accountApi.useSignOut();

  const handleSignOut = () => {
    signOut(undefined, {
      onSuccess: () => router.push(RoutePath.Home),
    });
  };

  if (!account) return null;

  return (
    <>
      <Head>
        <title>Profile</title>
      </Head>

      <Stack className={classes.main}>
        <Stack className={classes.header}>
          <Button
            variant="transparent"
            onClick={() => router.push(RoutePath.Home)}
            leftSection={<Icon type={IconType.ChevronCompactLeft} size={35} />}
          >
            <Text size="xl" c="text.8">
              Back
            </Text>
          </Button>

          <Stack w="100%" gap={40}>
            <Group wrap="nowrap">
              <Icon type={IconType.CircleAvatar} size={isMobile ? 74 : 114} color="green" />

              <Stack gap={20}>
                <Group>
                  <Title tt="uppercase" order={3}>
                    Mail:
                  </Title>
                  <Text size="xl">{account.email}</Text>
                </Group>
                <Group>
                  <Title tt="uppercase" order={3}>
                    Name:
                  </Title>
                  <Text size="xl">{account.name}</Text>
                </Group>
              </Stack>
            </Group>
          </Stack>

          <Group component="stack" gap={0} w="100%" wrap={isMobile ? 'wrap' : 'nowrap'}>
            <Button
              variant="filled"
              justify="space-between"
              onClick={handleSignOut}
              disabled={isSignOutPending}
              rightSection={<Icon type={IconType.CircleArrow} color="inherit" />}
              miw={isMobile ? 200 : 400}
              w={isMobile ? 200 : 400}
            >
              <Text size="lg">Log out</Text>
            </Button>

            <Group gap={0} align="center" w="100%" wrap="nowrap">
              <Divider color="text.8" orientation="horizontal" w="100%" />
              <Icon type={IconType.CircleArrowThin} size={isMobile ? 33 : 66} color="green" />
            </Group>
          </Group>
        </Stack>

        <Stack w="100%" gap={40}>
          <Group gap={10} justify="center" maw="80%">
            <Divider color="text.8" orientation="horizontal" w={isMobile ? 20 : 70} />

            <Text c="main.3" size="xl">
              Your courses
            </Text>

            <Divider color="text.8" orientation="horizontal" flex={1} />
          </Group>

          <Stack gap={20}>
            {[testCourse, testCourse, testCourse].map((course, index) => (
              <CoursePreview key={testCourse.id} course={course} index={index} />
            ))}
          </Stack>
        </Stack>
      </Stack>
    </>
  );
};

export default Profile;
