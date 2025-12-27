import { useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useMemo } from "react";
import { PATHS } from "@/app/routes/routes";
import { ADMIN_SIDEBAR_SECTIONS } from "./config";
import type { SidebarItem } from "@/shared/ui/sidebar"; // или твой тип item

export type AdminSidebarMode = "full" | "collapsed" | "hidden";

type SidebarSection<TItem> =
  | TItem[]
  | {
      title?: ReactNode;
      items: TItem[];
    };

const normalize = (p: string) => (p.length > 1 ? p.replace(/\/+$/, "") : p);
const starts = (prefix: string) => (p: string) => p.startsWith(prefix);

const HIDE_SIDEBAR_MATCHERS = [
  starts(PATHS.ADMIN_COURSE_DETAIL.clearPattern),
  starts(PATHS.ADMIN_LANDING_DETAIL.clearPattern),
  starts(PATHS.ADMIN_USER_DETAIL.clearPattern),
  starts(PATHS.ADMIN_AUTHOR_DETAIL.clearPattern),
  starts(PATHS.ADMIN_BOOK_DETAIL.clearPattern),
  starts(PATHS.ADMIN_BOOK_LANDING_DETAIL.clearPattern),
];

const normalizeSections = <TItem>(sections: SidebarSection<TItem>[]) =>
  sections.map((s) => (Array.isArray(s) ? { title: null, items: s } : s));

export const useAdminNav = () => {
  const { pathname } = useLocation();

  return useMemo(() => {
    const p = normalize(pathname);

    const sidebarMode: AdminSidebarMode = HIDE_SIDEBAR_MATCHERS.some((m) =>
      m(p),
    )
      ? "collapsed"
      : "full";

    const normalized = normalizeSections<SidebarItem>(ADMIN_SIDEBAR_SECTIONS);

    const currentTitleKey =
      normalized
        .flatMap((sec) => sec.items)
        .find((item) => p.startsWith(item.path))?.title ?? null;

    return { sidebarMode, currentTitleKey, pathname: p };
  }, [pathname]);
};
