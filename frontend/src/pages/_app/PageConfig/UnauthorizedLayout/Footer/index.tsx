import React, { FC, memo } from 'react';
import { Anchor, AppShell, Divider, Group, Stack, Text, Title } from '@mantine/core';

import { WhiteLogoImage } from 'public/images';

import Icon, { IconType } from 'components/Icon';
import classes from './index.module.css';

const POLITIES_ROUTES = [
  {
    href: '',
    title: 'Terns of Use',
  },
  {
    href: '',
    title: 'Cookie Policy',
  },
  {
    href: '',
    title: 'Privacy Policy',
  },
];

const PRODUCT_ROUTES = [
  {
    href: '',
    title: 'Home page',
  },
  {
    href: '',
    title: 'Tour',
  },
  {
    href: '',
    title: 'Templates',
  },
];

const Footer: FC = () => (
  <AppShell.Footer className={classes.footer}>
    <Stack pr={20} gap={10} flex={1} className={classes.stack}>
      <Group align="flex-start" wrap="nowrap" gap={40}>
        <Stack miw={150} gap={10}>
          <Title order={3} c="background.3">
            CONTACTS
          </Title>
          <Text size="md" c="background.3">
            X44G+755 - Mina Jebel Ali - Jabal Ali Industrial Second - Dubai - UAE
          </Text>
          <Text size="md" c="background.3">
            +971 55 633 5434
          </Text>
          <Anchor href="https://inform@di-s.org" target="_blank" underline="never">
            <Text size="md" c="background.3">
              inform@di-s.org
            </Text>
          </Anchor>
        </Stack>

        <Group gap={0} align="center" w="80%" flex={1} wrap="nowrap" miw={160}>
          <Divider color="background.3" orientation="horizontal" w="80%" maw={600} />
          <Icon type={IconType.CircleArrow} size={33} color="back" />
        </Group>
      </Group>

      <Divider color="background.3" orientation="horizontal" w="80%" maw={600} />

      <Group justify="space-between" gap={20} wrap="nowrap" w={300}>
        <Stack gap={10} w={150}>
          <Title order={4} c="background.3">
            POLITIES
          </Title>

          {POLITIES_ROUTES.map(({ href, title }) => (
            <Anchor key={title} underline="never" href={href}>
              <Text c="background.3" size="md">
                {title}
              </Text>
            </Anchor>
          ))}
        </Stack>

        <Stack gap={10} w={150}>
          <Title order={4} c="background.3">
            PRODUCT
          </Title>

          {PRODUCT_ROUTES.map(({ href, title }) => (
            <Anchor key={title} underline="never" href={href}>
              <Text c="background.3" size="md">
                {title}
              </Text>
            </Anchor>
          ))}
        </Stack>
      </Group>
    </Stack>

    <Group justify="flex-end" align="flex-end" mt="-25px" ml="-20px">
      <WhiteLogoImage />
    </Group>
  </AppShell.Footer>
);

export default memo(Footer);
