import { FC, ReactElement } from 'react';
import { AppShell, Center, Stack } from '@mantine/core';

import { LayoutTheme } from 'routes';
import { LAYOUT_THEME_SETTINGS, MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import { useMediaQuery } from '@mantine/hooks';
import Header from './Header';

import classes from './index.module.css';
import Footer from '../components/Footer';

interface MainLayoutProps {
  children: ReactElement;
  theme: LayoutTheme;
  mobileTheme?: LayoutTheme;
}

const MainLayout: FC<MainLayoutProps> = ({ children, theme, mobileTheme }) => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <AppShell
      component={Stack}
      className={classes.shell}
      bg={LAYOUT_THEME_SETTINGS[isMobile ? mobileTheme || theme : theme].bg}
    >
      <Header />

      <AppShell.Main className={classes.main}>
        <Center>{children}</Center>
      </AppShell.Main>

      <Footer />
    </AppShell>
  );
};

export default MainLayout;
