import { Stack, Text, Image, Group, Box, Button, ActionIcon, Tooltip, Divider, Title } from '@mantine/core';
import { NextPage } from 'next';
import Head from 'next/head';

import Icon, { IconType } from 'components/Icon';
import { modals } from '@mantine/modals';
import { ModalId } from 'types';
import FeedbackFormModal from 'components/FeedbackFormModal';
import modalClasses from 'components/Modal/index.module.css';
import { useMediaQuery } from '@mantine/hooks';
import classes from './index.module.css';
import CoursesButton from './components/CoursesButton';
import Search from './components/Search';
import Filter from './components/Filter';
import CoursesBlock from './components/CoursesBlock';
import FeedbackButton from './components/FeedbackButton';

const Home: NextPage = () => {
  const isMobile = useMediaQuery('(max-width: 400px)');

  return (
    <>
      <Head>
        <title>Home</title>
      </Head>

      <Stack flex={1} gap={isMobile ? 44 : 60}>
        <Group wrap="nowrap" justify="space-between" flex={1} gap={37}>
          <Search setParams={() => {}} />

          <Filter setParams={() => {}} />
        </Group>

        <Stack pos="relative" gap={0}>
          <Group wrap="nowrap">
            <Title order={1} tt="uppercase" c="text.8">
              Online
            </Title>
            <Title order={1} tt="uppercase" c="main.3">
              dental
            </Title>
          </Group>

          <Box className={classes.image}>
            <Title order={1} tt="uppercase" c="text.8">
              school
            </Title>
          </Box>

          <CoursesButton />

          {isMobile ? (
            <Image src="/images/dashboard.png" alt="image" />
          ) : (
            <Image src="/images/dashboard-desktop.png" alt="image" />
          )}
        </Stack>

        <Stack gap={1}>
          <Box mb={20}>
            <Text size="lg" c="text.8">
              The{' '}
              <Text size="lg" c="main.3" span>
                widest
              </Text>{' '}
              range <br />
              of products
            </Text>
          </Box>

          <Group gap={0}>
            <Button
              variant="filled"
              justify="space-between"
              rightSection={<Icon type={IconType.CircleArrow} color="inherit" />}
              miw={isMobile ? 200 : 400}
              w={isMobile ? 200 : 400}
            >
              <Text size="lg">Choose your course</Text>
            </Button>

            <Divider color="text.8" orientation="horizontal" flex={1} />
          </Group>

          <Stack className={classes.feedbackIcon} gap={4}>
            <Box>
              <Text size="lg" c="text.8" span fz={16}>
                Best{' '}
              </Text>
              <Text size="lg" c="main.3" span fz={16}>
                prices
              </Text>
            </Box>

            <FeedbackButton />
          </Stack>
        </Stack>

        <CoursesBlock />
      </Stack>
    </>
  );
};

export default Home;
