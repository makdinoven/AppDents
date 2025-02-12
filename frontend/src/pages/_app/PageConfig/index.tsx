import { FC, Fragment, ReactElement } from 'react';
import { useRouter } from 'next/router';

import { accountApi } from 'resources/account';

import { LayoutType, RoutePath, routesConfiguration, ScopeType } from 'routes';

import MainLayout from './MainLayout';
import PrivateScope from './PrivateScope';
import UnauthorizedLayout from './UnauthorizedLayout';

const layoutToComponent = {
  [LayoutType.MAIN]: MainLayout,
  [LayoutType.UNAUTHORIZED]: UnauthorizedLayout,
};

const scopeToComponent = {
  [ScopeType.PUBLIC]: Fragment,
  [ScopeType.PRIVATE]: PrivateScope,
};

interface PageConfigProps {
  children: ReactElement;
}

const PageConfig: FC<PageConfigProps> = ({ children }) => {
  const { route, push } = useRouter();

  const { data: account, isLoading: isAccountLoading } = accountApi.useGet();

  if (isAccountLoading) return null;

  const { scope, layout } = routesConfiguration[route as RoutePath] || {};
  let Scope = scope ? scopeToComponent[scope] : Fragment;
  let Layout = layout ? layoutToComponent[layout] : Fragment;

  if (scope === ScopeType.PRIVATE && !account) {
    push(RoutePath.Home);
    return null;
  }

  if (scope === ScopeType.PUBLIC && account) {
    Scope = scopeToComponent[ScopeType.PRIVATE];
  }

  if (route === RoutePath.Home || (route === RoutePath.Course && !account)) {
    Scope = scopeToComponent[ScopeType.PUBLIC];
    Layout = layoutToComponent[LayoutType.UNAUTHORIZED];
  }

  return (
    <Scope>
      <Layout>{children}</Layout>
    </Scope>
  );
};

export default PageConfig;
