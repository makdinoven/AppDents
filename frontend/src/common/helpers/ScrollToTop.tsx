import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { AUTH_MODAL_ROUTES } from "./commonConstants.ts";
import { Path } from "../../routes/routes.ts";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  const prevPathname = useRef<string | null>(null);
  const dontScrollLinks = [
    Path.search,
    Path.payment,
    Path.cart,
    ...AUTH_MODAL_ROUTES,
  ];

  useEffect(() => {
    const isPrevAuthRoute = prevPathname.current
      ? dontScrollLinks.some((link) => prevPathname.current?.startsWith(link))
      : false;
    const isCurrentAuthRoute = dontScrollLinks.some((link) =>
      pathname.startsWith(link),
    );

    if (!isPrevAuthRoute && !isCurrentAuthRoute) {
      window.scrollTo(0, 0);
    }

    prevPathname.current = pathname;
  }, [pathname]);

  return null;
};

export default ScrollToTop;
