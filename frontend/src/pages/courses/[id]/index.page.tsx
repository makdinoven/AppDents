import { Badge, Box, Button, Divider, Grid, Group, Stack, Text, Title } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';
import Head from 'next/head';

import { useRouter } from 'next/router';
import { RoutePath } from 'routes';
import DividerTitle from 'components/DividerTitle';
import { ColoredPaper } from 'components';
import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import classes from './index.module.css';
import Header from './components/Header';
import ShortInfoSection from './components/ShortInfo';
import LessonPreview from './components/LessonPreview';
import PurchaseButton from './components/PurchaseButton';
import ProfessorsSection from './components/ProfessorsSection';

const testCourse = {
  id: 1,
  name: 'Damon 2.0 How to treat all common malocclusions',
  description: 'A comprehensive course on essential dental knowledge and practices.',
  sections: [
    {
      id: 1,
      title: 'Introduction to Dentistry',
      duration: '15 minutes',
      info: ['Overview of teeth structure and oral cavity anatomy.', 'Best practices for maintaining oral health.'],
    },
    {
      id: 2,
      title: 'Clinical Procedures',
      duration: '30 minutes',
      info: ['Overview of teeth structure and oral cavity anatomy.', 'Best practices for maintaining oral health.'],
    },
  ],
};

const Course = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  const router = useRouter();

  const rightTopOffset = { w: 332, h: 176 };
  const leftTopOffset = { w: 332, h: 176 };

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

        <Stack w="100%" gap={140}>
          <Header course={testCourse} />

          <Stack gap={40}>
            <DividerTitle maw="80%">About this course</DividerTitle>

            <ShortInfoSection />
          </Stack>

          <Stack gap={40}>
            <DividerTitle maw="80%">Course program</DividerTitle>

            <Box h={850}>
              <ColoredPaper
                rightTopOffset={rightTopOffset}
                childrenClassName={classes.coloredPaper}
                color="secondarySkyBlue"
              >
                <Stack className={classes.courseProgram}>
                  <Group wrap="nowrap">
                    <Title order={2} c="background.3">
                      {testCourse.name}
                    </Title>

                    <Badge variant="outline" color="text.8" size="xl">
                      <Text size="lg" c="text.8">
                        8 online lessons
                      </Text>
                    </Badge>
                  </Group>

                  <Divider color="text.8" maw="60%" />

                  <Stack>
                    <Text size="xl" c="text.8">
                      A course on how to treat all common malocclusions using the Damon protocols.
                    </Text>

                    <Text size="xl" c="text.8">
                      During the training you will learn:
                    </Text>

                    {[1].map(() => (
                      <Group wrap="nowrap">
                        <Icon type={IconType.CircleArrowThin} color="green" size={30} />

                        <Text>
                          Detailed protocols for the treatment of Class II, Class III, deep, open and crossbite, teeth
                          impaction, gummy smile
                        </Text>
                      </Group>
                    ))}
                  </Stack>
                </Stack>
              </ColoredPaper>
            </Box>

            <Group h={500} w="100%" align="center" pos="relative" top={-350} px="10%">
              <ColoredPaper color="glass">
                <Grid px={105} pt={49} columns={2}>
                  {[1, 2].map(() => (
                    <Grid.Col span={1}>
                      <Stack>
                        <Group wrap="nowrap">
                          <Box maw={30}>
                            <Icon type={IconType.CircleArrowThin} color="back" size={30} />
                          </Box>

                          <Text size="md" c="background.3">
                            Detailed protocols for the treatment of Class II, Class III, deep, open and crossbite, teeth
                            impaction, gummy smile
                          </Text>
                        </Group>

                        <Divider w="50%" c="background.3" />
                      </Stack>
                    </Grid.Col>
                  ))}
                </Grid>
              </ColoredPaper>
            </Group>

            <Stack w="80%">
              <Text size="xl" c="text.8">
                You can buy the{' '}
                <Text c="main.3" component="span">
                  entire course
                </Text>{' '}
                now at the new price -{' '}
                <Text c="main.3" component="span">
                  $19
                </Text>
                , instead of the old one - $312
              </Text>

              <PurchaseButton />
            </Stack>
          </Stack>

          <Stack gap={40}>
            <DividerTitle maw="80%">The full course program</DividerTitle>

            <Stack gap={203}>
              {testCourse.sections.map((lesson) => (
                <LessonPreview key={lesson.id} title={lesson.title} duration={lesson.duration} info={lesson.info} />
              ))}
            </Stack>
          </Stack>

          <Stack gap={40}>
            <DividerTitle maw="80%">Professors</DividerTitle>

            <ProfessorsSection />
          </Stack>

          <Box h={677}>
            <ColoredPaper
              leftTopOffset={leftTopOffset}
              childrenClassName={classes.coloredPaper}
              color="secondarySkyBlue"
            >
              <Stack gap={80} align="flex-start" py={44} px={51}>
                <Title order={3} tt="uppercase" c="main.3" mb={31}>
                  Special offer
                </Title>

                <Stack gap={20} w="100%">
                  <Title order={2} tt="uppercase" c="text.8">
                    {testCourse.name}
                  </Title>

                  <Text size="lg" c="text.8">
                    {testCourse.description}
                  </Text>

                  <Group gap={0} align="center" w="80%" flex={1} wrap="nowrap" miw={160}>
                    <Divider color="text.8" orientation="horizontal" w="80%" maw={600} />
                    <Icon type={IconType.CircleArrowThin} size={isMobile ? 33 : 66} color="green" />
                  </Group>
                </Stack>

                <Stack gap={20} w="100%" align="center">
                  <Group gap={20} align="center" w="100%" flex={1} wrap="nowrap" miw={160}>
                    <Icon type={IconType.Clock} size={isMobile ? 33 : 44} color="back" />

                    <Title order={2} c="background.3" tt="uppercase">
                      Access to the course is unlimited in time!
                    </Title>
                  </Group>

                  <PurchaseButton />
                </Stack>
              </Stack>
            </ColoredPaper>
          </Box>
        </Stack>
      </Stack>
    </>
  );
};

export default Course;
