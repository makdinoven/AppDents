import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { AUTH_MODAL_ROUTES } from "./commonConstants.ts";
import { Path } from "../../routes/routes.ts";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  const prevPathname = useRef<string | null>(null);
  const dontScrollLinks = [Path.search, Path.cart, ...AUTH_MODAL_ROUTES];

  useEffect(() => {
    const isPrevAuthRoute = prevPathname.current
      ? dontScrollLinks.includes(prevPathname.current)
      : false;
    const isCurrentAuthRoute = dontScrollLinks.includes(pathname);

    if (!isPrevAuthRoute && !isCurrentAuthRoute) {
      window.scrollTo(0, 0);
    }

    prevPathname.current = pathname;
  }, [pathname]);

  return null;
};

export default ScrollToTop;
