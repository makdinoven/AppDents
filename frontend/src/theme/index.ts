import { Rethink_Sans } from 'next/font/google';
import { createTheme, DEFAULT_THEME } from '@mantine/core';

import * as components from './components';
import { colors } from './colors';

const rethinkSans = Rethink_Sans({ subsets: ['latin'] });

const theme = createTheme({
  components,
  fontFamily: rethinkSans.style.fontFamily,
  fontFamilyMonospace: 'monospace',
  headings: {
    fontFamily: `${rethinkSans.style.fontFamily}, ${DEFAULT_THEME.fontFamily}`,
    fontWeight: '600',
  },
  colors,
  primaryColor: 'main',
  primaryShade: {
    light: 5,
    dark: 0,
  },
  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '16px',
    xl: '32px',
  },
  fontSizes: {
    h2: '28px',
    h3: '24px',
    h4: '20px',
    regular: '16px',
    small: '14px',
    caption: '12px',
  },
  other: {
    transition: {
      speed: {
        fast: '200ms',
        smooth: '300ms',
        slow: '400ms',
        slowest: '1000ms',
      },
      easing: {
        linear: 'linear',
        ease: 'ease',
        easeIn: 'ease-in',
        easeOut: 'ease-out',
        easeInOut: 'ease-in-out',
        easeInBack: 'cubic-bezier(0.82,-0.2, 0.32, 1.84)',
        easeOutBack: 'cubic-bezier(0.5,-1.18, 0.51, 1.11)',
        easeInOutBack: 'cubic-bezier(.64,-0.56,.34,1.55)',
      },
    },
    weight: {
      regular: '400',
      medium: '500',
      semiBold: '600',
      bold: '700',
      extraBold: '800',
    },
    fontFamilyBodyText: 'Open Sans, sans-serif',
  },
});

export default theme;
