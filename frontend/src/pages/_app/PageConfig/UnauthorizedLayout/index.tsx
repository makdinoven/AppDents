import { FC, ReactElement } from 'react';
import { AppShell, Center, Stack } from '@mantine/core';

import classes from './index.module.css';
import Header from './Header';
import Footer from './Footer';

interface UnauthorizedLayoutProps {
  children: ReactElement;
}

const UnauthorizedLayout: FC<UnauthorizedLayoutProps> = ({ children }) => (
  <AppShell component={Stack} className={classes.main} bg="background.3">
    <Header />

    <AppShell.Main pt={47} px={20}>
      <Center px={20}>{children}</Center>
    </AppShell.Main>

    <Footer />
  </AppShell>
);

export default UnauthorizedLayout;
