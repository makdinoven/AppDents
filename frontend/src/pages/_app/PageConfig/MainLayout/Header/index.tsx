import { FC, memo } from 'react';
import Link from 'next/link';
import { Anchor, AppShell, Group } from '@mantine/core';

import { accountApi } from 'resources/account';

import { RoutePath } from 'routes';

import { BlackLogoImage } from 'public/images';

import { Icon } from 'components';
import { IconType } from 'components/Icon';
import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import classes from './index.module.css';

const Header: FC = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  const { data: account } = accountApi.useGet();

  if (!account) return null;

  return (
    <AppShell.Header className={classes.header}>
      <Group justify="space-between" align="center" w="100%">
        <Anchor component={Link} href={RoutePath.Home} className={classes.logo}>
          <BlackLogoImage />
        </Anchor>

        <Anchor component={Link} href={RoutePath.Profile} className={classes.avatar}>
          <Icon type={IconType.CircleFilledAvatar} size={isMobile ? 34 : 58} color="greenBackground" />
        </Anchor>
      </Group>
    </AppShell.Header>
  );
};

export default memo(Header);
