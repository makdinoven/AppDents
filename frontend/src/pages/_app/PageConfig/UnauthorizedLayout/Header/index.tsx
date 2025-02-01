import React, { FC, memo } from 'react';
import Link from 'next/link';
import { Anchor, AppShell, Button, Group, Title } from '@mantine/core';

import { BlackLogoImage } from 'public/images';

import { RoutePath } from 'routes';

import classes from './index.module.css';

const Header: FC = () => (
  <AppShell.Header className={classes.header}>
    <Group justify="space-between" align="center" w="100%">
      <Anchor component={Link} href={RoutePath.Home} h={30}>
        <BlackLogoImage h={30} />
      </Anchor>

      <Button variant="transparent" p={0}>
        <Title order={3} c="text.8">
          LOG IN
        </Title>
      </Button>
    </Group>
  </AppShell.Header>
);

export default memo(Header);
