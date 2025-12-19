import { ReactNode, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { AUTH_MODAL_ROUTES } from "@/shared/common/helpers/commonConstants.ts";
import { PATHS } from "../routes.ts";

export const ScrollToTopProvider = ({ children }: { children: ReactNode }) => {
  const { pathname } = useLocation();
  const prevPathname = useRef<string | null>(null);
  const dontScrollLinks = [
    PATHS.SEARCH,
    PATHS.PAYMENT,
    PATHS.CART,
    PATHS.PROFILE_INVITED_USERS,
    PATHS.PROFILE_MY_COURSES,
    PATHS.PROFILE_MY_BOOKS,
    PATHS.PROFILE_PURCHASE_HISTORY,
    PATHS.SUPPORT,
    PATHS.SUPPORT_CHAT.pattern,
    PATHS.PROFILE_COURSE_LESSON.pattern,
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

  return children;
};
