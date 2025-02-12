import { Divider, Group, Text } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import { ReactNode } from 'react';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';

type DividerTitleProps = {
  children: string | ReactNode;
  maw?: string;
};

const DividerTitle = ({ children, maw = '100%' }: DividerTitleProps) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <Group gap={10} justify="center" maw={maw}>
      <Divider color="text.8" orientation="horizontal" w={isMobile ? 20 : 70} />

      <Text c="main.3" size="xl">
        {children}
      </Text>

      <Divider color="text.8" orientation="horizontal" flex={1} />
    </Group>
  );
};

export default DividerTitle;
