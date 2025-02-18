export enum ScopeType {
  PUBLIC = 'PUBLIC',
  PRIVATE = 'PRIVATE',
}

export enum LayoutType {
  MAIN = 'MAIN',
  UNAUTHORIZED = 'UNAUTHORIZED',
}

export enum LayoutTheme {
  MAIN = 'MAIN',
  WHITE = 'WHITE',
}

export enum RoutePath {
  Profile = '/profile',
  Home = '/',
  Courses = '/courses',
  Course = '/courses/[id]',
  NotFound = '/404',
}

type RoutesConfiguration = {
  [routePath in RoutePath]: {
    scope?: ScopeType;
    layout?: LayoutType;
    theme?: LayoutTheme;
    mobileTheme?: LayoutTheme;
  };
};

export const routesConfiguration: RoutesConfiguration = {
  [RoutePath.Profile]: {
    scope: ScopeType.PRIVATE,
    layout: LayoutType.MAIN,
    theme: LayoutTheme.MAIN,
  },

  [RoutePath.Home]: {
    scope: ScopeType.PUBLIC,
    layout: LayoutType.MAIN,
    theme: LayoutTheme.MAIN,
  },

  [RoutePath.Courses]: {
    scope: ScopeType.PUBLIC,
    layout: LayoutType.MAIN,
    theme: LayoutTheme.MAIN,
  },

  [RoutePath.Course]: {
    scope: ScopeType.PUBLIC,
    layout: LayoutType.MAIN,
    theme: LayoutTheme.MAIN,
    mobileTheme: LayoutTheme.WHITE,
  },

  [RoutePath.NotFound]: {},
};
