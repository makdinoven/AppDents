import React, { FC, memo } from 'react';
import Link from 'next/link';
import { Anchor, AppShell, Button, Group, Title } from '@mantine/core';

import { BlackLogoImage } from 'public/images';

import { RoutePath } from 'routes';
import { Icon, SignInModal } from 'components';
import { useDisclosure } from '@mantine/hooks';
import { modals } from '@mantine/modals';

import modalClasses from 'components/Modal/index.module.css';
import { IconType } from 'components/Icon';
import { ModalId } from 'types';
import classes from './index.module.css';

const Header: FC = () => {
  const [openedSignInModal, { toggle: toggleSignInModal, close: closeSignInModal }] = useDisclosure(false);

  return (
    <AppShell.Header className={classes.header}>
      <Group justify="space-between" align="center" w="100%">
        <Anchor component={Link} href={RoutePath.Home} h={30}>
          <BlackLogoImage h={30} />
        </Anchor>

        <Button
          variant="transparent"
          p={0}
          onClick={() => {
            modals.closeAll();
            modals.open({
              modalId: ModalId.SIGN_IN,
              children: <SignInModal onClose={() => modals.close(ModalId.SIGN_IN)} />,
              size: 'xl',
              withCloseButton: false,
              classNames: {
                header: modalClasses.header,
                content: modalClasses.content,
                body: modalClasses.body,
                root: modalClasses.root,
              },
              yOffset: 41,
              overlayProps: {
                backgroundOpacity: 0.55,
                blur: 3,
              },
            });
          }}
        >
          <Title order={3} c="text.8">
            LOG IN
          </Title>
        </Button>
      </Group>
    </AppShell.Header>
  );
};
export default memo(Header);
