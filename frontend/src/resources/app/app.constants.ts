import { LayoutTheme } from 'routes';

export const MOBILE_SCREEN_PX = 460;

export const LAYOUT_THEME_SETTINGS: Record<LayoutTheme, { bg: string }> = {
  [LayoutTheme.MAIN]: {
    bg: 'background.3',
  },
  [LayoutTheme.WHITE]: {
    bg: 'white',
  },
};
