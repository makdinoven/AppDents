import { Box, Divider, Group, Stack, Title, Text, Image, Center } from '@mantine/core';
import { ColoredPaper, Icon } from 'components';
import { IconType } from 'components/Icon';

import { Landing } from 'resources/landing/landing.types';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { useMediaQuery } from '@mantine/hooks';
import classes from './index.module.css';
import PurchaseButton from '../PurchaseButton';

type HeaderProps = {
  landing: Landing;
};

const Header = ({ landing }: HeaderProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);
  const rightTopOffset = isMobile ? { w: 172, h: 64 } : { w: 325, h: 120 };
  const leftBottomOffset = isMobile ? { w: 110, h: 100 } : { w: 190, h: 208 };

  return (
    <Group w="100%" wrap={isMobile ? 'wrap' : 'nowrap'} justify="start" align="start" gap={20}>
      <Box w={isMobile ? '100%' : '50%'}>
        <ColoredPaper
          rightTopOffset={rightTopOffset}
          leftBottomOffset={leftBottomOffset}
          childrenClassName={classes.childrenClassName}
          header={
            isMobile ? (
              <Title order={1} c="text.8" tt="uppercase" pos="relative" ta="end" top={-40}>
                online <br /> course
              </Title>
            ) : undefined
          }
        >
          <Box h={`calc(${isMobile ? 308 : 578}px - ${leftBottomOffset.h + rightTopOffset.h}px)`} pos="relative">
            <Center>
              <Image
                src="/images/course-image.png"
                alt="Demo"
                radius={20}
                width="90%"
                fit="contain"
                className={classes.imageBox}
              />
            </Center>
          </Box>
        </ColoredPaper>
      </Box>

      <Stack w={isMobile ? '100%' : '50%'} justify="space-between">
        <Stack w="100%" pos="relative" gap={20}>
          {!isMobile && (
            <Title order={1} c="text.8" tt="uppercase" pos="relative" textWrap="nowrap" right="50%">
              online course
            </Title>
          )}

          <Divider color="text.8" orientation="horizontal" w="100%" h={1} />

          <Title order={2} c="main.3" tt="uppercase">
            {landing.title}
          </Title>

          <Group gap={0} align="center" w="80%" flex={1} wrap="nowrap" miw={160}>
            <Divider color="text.8" orientation="horizontal" h={2} w={isMobile ? '80%' : '50%'} maw={600} />
            <Icon type={IconType.CircleArrowThin} size={isMobile ? 33 : 66} color="green" />
          </Group>

          <Text size="lg" c="text.8">
            {landing.main_text}
          </Text>
        </Stack>

        <PurchaseButton landing={landing} />
      </Stack>
    </Group>
  );
};

export default Header;
