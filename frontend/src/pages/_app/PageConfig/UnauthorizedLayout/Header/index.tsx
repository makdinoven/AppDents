import React, { FC, memo } from 'react';
import Link from 'next/link';
import { Anchor, AppShell, Box, Group, Title } from '@mantine/core';

import { BlackLogoImage } from 'public/images';

import { RoutePath } from 'routes';
import { Popover } from 'components';
import AuthPopover from 'components/AuthPopover';

import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import classes from './index.module.css';

const Header: FC = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  const floatingSizes = isMobile ? { w: 89, h: 58 } : { w: 133, h: 70, offset: -55 };

  return (
    <AppShell.Header className={classes.header}>
      <Group justify="space-between" align="center" w="100%">
        <Anchor component={Link} href={RoutePath.Home} className={classes.logo}>
          <BlackLogoImage />
        </Anchor>

        <Popover
          target={
            <Title order={3} c="text.8">
              LOG IN
            </Title>
          }
          floatingSizes={floatingSizes}
        >
          <Box className={classes.loginButton}>
            <AuthPopover />
          </Box>
        </Popover>
      </Group>
    </AppShell.Header>
  );
};

export default memo(Header);
