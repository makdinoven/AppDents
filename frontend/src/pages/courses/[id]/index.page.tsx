import { Divider, Group, Loader, Stack, Text } from '@mantine/core';
import Head from 'next/head';

import { useRouter } from 'next/router';
import { RoutePath } from 'routes';
import DividerTitle from 'components/DividerTitle';
import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { landingApi } from 'resources/landing';
import BackButton from 'components/BackButton';
import classes from './index.module.css';
import Header from './components/Header';
import ShortInfoSection from './components/ShortInfo';
import LessonPreview from './components/LessonPreview';
import PurchaseButton from './components/PurchaseButton';
import ProfessorsSection from './components/ProfessorsSection';
import CourseProgram from './components/CourseProgram';
import SpecialOffer from './components/SpecialOffer';

const Course = () => {
  const { push, query } = useRouter();

  const { data: landing, isLoading: isLandingLoading } = landingApi.useGet(query?.id as string);
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  if (!landing || isLandingLoading) {
    return <Loader />;
  }

  return (
    <>
      <Head>
        <title>{landing.title}</title>
      </Head>

      <Stack className={classes.root}>
        <BackButton onClick={() => push(RoutePath.Home)} />

        <Stack className={classes.main}>
          <Stack className={classes.info}>
            <Header landing={landing} />

            <ShortInfoSection />

            <CourseProgram landing={landing} />

            <Stack w="100%" className={classes.buyBtn}>
              <Text size="xl" c="text.8" className={classes.buyBtnText}>
                You can buy the{' '}
                <Text c="main.3" component="span">
                  entire course
                </Text>{' '}
                now at the new price -{' '}
                <Text c="main.3" component="span">
                  ${landing.price}
                </Text>
                , instead of the old one - ${landing.old_price}
              </Text>

              <Group gap={0} w="100%">
                <PurchaseButton landing={landing} />

                <Divider color="text.8" orientation="horizontal" flex={1} />
              </Group>
            </Stack>
          </Stack>

          <Stack className={classes.courseProgram}>
            <DividerTitle maw={isMobile ? '100%' : '80%'}>The full course program</DividerTitle>

            <Stack className={classes.coursesStack}>
              {landing.modules.map((module) => (
                <LessonPreview key={module.id} module={module} landing={landing} />
              ))}
            </Stack>
          </Stack>

          <ProfessorsSection />

          <SpecialOffer landing={landing} />
        </Stack>
      </Stack>
    </>
  );
};

export default Course;
