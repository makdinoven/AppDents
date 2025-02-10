import { FC, memo } from 'react';
import Link from 'next/link';
import { Anchor, AppShell, Group } from '@mantine/core';

import { accountApi } from 'resources/account';

import { RoutePath } from 'routes';

import UserMenu from './components/UserMenu';

const Header: FC = () => {
  const { data: account } = accountApi.useGet();

  if (!account) return null;

  return (
    <AppShell.Header>
      <Group h={72} px={32} py={0} justify="space-between" bg="white">
        <Anchor component={Link} href={RoutePath.Home} />

        <UserMenu />
      </Group>
    </AppShell.Header>
  );
};

export default memo(Header);
