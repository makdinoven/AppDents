import { FC, ReactElement } from 'react';
import { AppShell, Center, Stack } from '@mantine/core';

import Header from './Header';

import classes from './index.module.css';
import Footer from '../components/Footer';

interface MainLayoutProps {
  children: ReactElement;
}

const MainLayout: FC<MainLayoutProps> = ({ children }) => (
  <AppShell component={Stack} className={classes.shell} bg="background.3">
    <Header />

    <AppShell.Main className={classes.main}>
      <Center>{children}</Center>
    </AppShell.Main>

    <Footer />
  </AppShell>
);

export default MainLayout;
