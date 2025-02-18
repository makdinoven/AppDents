import { Group, Text, Grid, Stack } from '@mantine/core';
import Icon, { IconType } from 'components/Icon';

import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { DividerTitle } from 'components';

type InfoItemProps = { icon: IconType; text: string; isMobile?: boolean };

const InfoItem = ({ icon, text, isMobile }: InfoItemProps) => (
  <Group wrap="nowrap" gap={isMobile ? 20 : 43}>
    <Icon type={icon} size={isMobile ? 33 : 58} color="secondaryBlue" style={{ minWidth: isMobile ? 33 : 58 }} />

    <Text size="xl" c="secondaryBlue.5">
      {text}
    </Text>
  </Group>
);

const ShortInfoSection = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  const infoData: { icon: IconType; text: string }[] = [
    {
      icon: IconType.Book,
      text: '8 lessons',
    },
    {
      icon: IconType.Percent,
      text: '94% discount',
    },
    {
      icon: IconType.Clock,
      text: 'Access to the course is not limited in time',
    },
    {
      icon: IconType.Glasses,
      text: '6 professors',
    },
    {
      icon: IconType.Money,
      text: '$293 savings',
    },
  ];

  return (
    <Stack gap={40}>
      <DividerTitle maw="80%">About this course</DividerTitle>

      <Grid columns={isMobile ? 1 : 3}>
        {infoData.map(({ icon, text }, index) => (
          <Grid.Col span={1} order={index + 1}>
            <InfoItem icon={icon} text={text} isMobile={isMobile} />
          </Grid.Col>
        ))}
      </Grid>
    </Stack>
  );
};

export default ShortInfoSection;
