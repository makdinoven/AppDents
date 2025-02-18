import { Badge, Box, Divider, Grid, Group, Stack, Title, Text } from '@mantine/core';

import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { DividerTitle, ColoredPaper, Icon } from 'components';
import { IconType } from 'components/Icon';

import { Landing } from 'resources/landing/landing.types';
import classes from './index.module.css';

type CourseProgramProps = {
  landing: Landing;
};

const CourseProgram = ({ landing }: CourseProgramProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);
  const rightTopOffset = isMobile ? { w: 183, h: 57 } : { w: 332, h: 176 };

  return (
    <Stack gap={40}>
      <DividerTitle maw="80%">Course program</DividerTitle>

      <Stack gap={0} mb={isMobile ? '-260px' : '-160px'}>
        <ColoredPaper
          rightTopOffset={rightTopOffset}
          childrenClassName={classes.coloredPaper}
          color="secondarySkyBlue"
          header={
            <Group wrap="nowrap" pt={isMobile ? 10 : 72} px={isMobile ? 0 : 35} w="100%" align="start" justify="end">
              {!isMobile && (
                <Title order={2} c="background.3" flex={1}>
                  {landing.title}
                </Title>
              )}

              <Badge variant="outline" color="text.8" size="xl">
                <Text size="lg" c="text.8">
                  8 online lessons
                </Text>
              </Badge>
            </Group>
          }
        >
          <Stack className={classes.courseProgram}>
            {isMobile && (
              <Title order={2} c="background.3" flex={1}>
                {landing.title}
              </Title>
            )}

            <Divider color="text.8" maw="60%" />

            <Stack gap={29}>
              <Text size="xl" c="text.8">
                {landing.main_text}
              </Text>

              <Text size="xl" c="text.8">
                During the training you will learn:
              </Text>

              <Stack gap={20}>
                {[1, 3, 4, 5].map(() => (
                  <Group wrap="nowrap" align="start">
                    <Box miw={isMobile ? 20 : 30}>
                      <Icon type={IconType.CircleArrowThin} color="green" size={isMobile ? 20 : 30} />
                    </Box>

                    <Text size="xl" flex={1} c="text.8">
                      Detailed protocols for the treatment of Class II, Class III, deep, open and crossbite, teeth
                      impaction, gummy smile
                    </Text>
                  </Group>
                ))}
              </Stack>
            </Stack>
          </Stack>
        </ColoredPaper>

        <Group w="100%" align="center" pos="relative" top={-250} px="10%">
          <ColoredPaper color="glass">
            <Grid px={isMobile ? 30 : 105} pt={isMobile ? 30 : 49} columns={isMobile ? 1 : 2} mih={500}>
              {[1, 2].map(() => (
                <Grid.Col span={1}>
                  <Stack gap={10}>
                    <Group wrap="nowrap">
                      <Text size="md" c="background.3">
                        Detailed protocols for the treatment of Class II, Class III, deep, open and crossbite, teeth
                        impaction, gummy smile
                      </Text>
                    </Group>

                    <Divider w={isMobile ? '100%' : '50%'} c="background.3" />
                  </Stack>
                </Grid.Col>
              ))}
            </Grid>
          </ColoredPaper>
        </Group>
      </Stack>
    </Stack>
  );
};

export default CourseProgram;
