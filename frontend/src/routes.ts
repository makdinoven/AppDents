export enum ScopeType {
  PUBLIC = 'PUBLIC',
  PRIVATE = 'PRIVATE',
}

export enum LayoutType {
  MAIN = 'MAIN',
  UNAUTHORIZED = 'UNAUTHORIZED',
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
  };
};

export const routesConfiguration: RoutesConfiguration = {
  [RoutePath.Profile]: {
    scope: ScopeType.PRIVATE,
    layout: LayoutType.MAIN,
  },

  [RoutePath.Home]: {
    scope: ScopeType.PUBLIC,
    layout: LayoutType.MAIN,
  },

  [RoutePath.Courses]: {
    scope: ScopeType.PUBLIC,
    layout: LayoutType.MAIN,
  },

  [RoutePath.Course]: {
    scope: ScopeType.PUBLIC,
    layout: LayoutType.MAIN,
  },

  [RoutePath.NotFound]: {},
};
