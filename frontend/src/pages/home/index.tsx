import { Stack, Text, Image, Group, Box, Button, ActionIcon, Tooltip, Divider, Title } from '@mantine/core';
import { NextPage } from 'next';
import Head from 'next/head';

import Icon, { IconType } from 'components/Icon';
import Modal from 'components/Modal';
import ResetPasswordModal from 'components/ResetPasswordModal';
import { SignInModal } from 'components';
import classes from './index.module.css';
import CoursesButton from './components/CoursesButton';
import Search from './components/Search';
import Filter from './components/Filter';
import CoursesBlock from './components/CoursesBlock';

const Home: NextPage = () => (
  <>
    <Head>
      <title>Home</title>
    </Head>

    <Stack flex={1}>
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
            courses
          </Title>
        </Group>

        <Box className={classes.image}>
          <Title order={1} tt="uppercase" c="text.8">
            school
          </Title>
        </Box>

        <CoursesButton />

        <Image src="/images/dashboard.png" alt="image" />
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
            rightSection={<Icon type={IconType.CircleArrow} color="inherit" size={20} />}
            miw={200}
            w={200}
          >
            Choose your course
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

          <Tooltip
            withArrow
            label="Can't find the course you need? Fill out the form and we'll help you."
            position="bottom"
            arrowSize={15}
            multiline
          >
            <ActionIcon w={65} h={65} radius="100%" variant="filled">
              <Icon type={IconType.Dialog} size={30} color="inherit" />
            </ActionIcon>
          </Tooltip>
        </Stack>
      </Stack>

      <CoursesBlock />
    </Stack>
  </>
);

export default Home;
