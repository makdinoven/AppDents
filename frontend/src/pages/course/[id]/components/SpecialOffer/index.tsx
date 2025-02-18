import { Box, Divider, Group, Stack, Title, Text } from '@mantine/core';

import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { ColoredPaper, Icon } from 'components';
import { IconType } from 'components/Icon';

import { Landing } from 'resources/landing/landing.types';
import classes from './index.module.css';
import PurchaseButton from '../PurchaseButton';

type CourseProgramProps = {
  landing: Landing;
};

const SpecialOffer = ({ landing }: CourseProgramProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  const leftTopOffset = isMobile ? { w: 195, h: 60 } : { w: 332, h: 176 };

  return (
    <ColoredPaper
      leftTopOffset={leftTopOffset}
      childrenClassName={classes.coloredPaper}
      color="secondarySkyBlue"
      header={
        <Box p={isMobile ? 14 : 44} px={isMobile ? 24 : 51}>
          <Title order={3} tt="uppercase" c="main.3">
            Special offer
          </Title>
        </Box>
      }
    >
      <Stack gap={80} align="flex-start" py={44} px={51}>
        <Stack gap={20} w="100%">
          <Title order={2} tt="uppercase" c="text.8">
            {landing.title}
          </Title>

          <Text size="lg" c="text.8">
            {landing.main_text}
          </Text>

          <Group gap={0} align="center" w="80%" flex={1} wrap="nowrap" miw={160}>
            <Divider color="text.8" orientation="horizontal" w="80%" maw={600} />
            <Icon type={IconType.CircleArrowThin} size={isMobile ? 33 : 66} color="green" />
          </Group>
        </Stack>

        <Stack gap={20} w="100%" align="center">
          <Group gap={20} align="center" w="100%" flex={1} wrap="nowrap" miw={160}>
            <Icon type={IconType.Clock} size={isMobile ? 33 : 44} color="back" />

            <Title order={2} c="background.3" tt="uppercase" flex={1}>
              Access to the course is unlimited in time!
            </Title>
          </Group>

          <PurchaseButton landing={landing} />
        </Stack>
      </Stack>
    </ColoredPaper>
  );
};

export default SpecialOffer;
