import { Route, Routes, useLocation } from "react-router-dom";
import { AUTH_MODAL_ROUTES } from "../../../shared/common/helpers/commonConstants.ts";
import AuthModalManager from "../../../shared/components/AuthModalManager/AuthModalManager.tsx";
import Cart from "../../../pages/Cart/Cart.tsx";
import SearchPage from "../../../pages/SearchPage/SearchPage.tsx";
import { PATHS } from "../routes.ts";
import { routesConfig } from "../router.tsx";

export const RouterProvider = () => {
  const location = useLocation();
  const backgroundLocation = location.state?.backgroundLocation || null;
  const isAuthModalRoute = AUTH_MODAL_ROUTES.includes(location.pathname);
  const isCartPage = location.pathname === PATHS.CART;
  const isSearchPage = location.pathname === PATHS.SEARCH;

  const renderRoutes = (configs: any) =>
    configs.map((route: any, idx: any) => {
      const { children, element, ...rest } = route;

      return (
        <Route key={idx} {...rest} element={element}>
          {children && renderRoutes(children)}
        </Route>
      );
    });

  return (
    <>
      <Routes location={backgroundLocation || location}>
        {renderRoutes(routesConfig)}
      </Routes>
      {(backgroundLocation || isAuthModalRoute) && <AuthModalManager />}
      {isCartPage && <Cart />}
      {isSearchPage && <SearchPage />}
    </>
  );
};
