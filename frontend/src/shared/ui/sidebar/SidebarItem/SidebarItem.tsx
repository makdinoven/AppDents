import s from "./SidebarItem.module.scss";
import { NavLink } from "react-router-dom";
import { t } from "i18next";
import { Chevron } from "@/shared/assets/icons";
import { ReactNode } from "react";

export type SidebarItem = {
  path: string;
  title: string;
  icon?: ReactNode;
  isCollapsed?: boolean;
};

export const SidebarItem = ({
  item,
  onClick,
  isCollapsed = false,
}: {
  item: SidebarItem;
  onClick: () => void;
  isCollapsed: boolean;
}) => {
  const icon = !!item.icon && <span className={s.icon}>{item.icon}</span>;

  const renderContent = isCollapsed ? (
    icon
  ) : (
    <>
      {item.icon && <span className={s.icon}>{item.icon}</span>}
      <span className={s.title}>{t(item.title)}</span>
      <Chevron className={s.arrow} />
    </>
  );

  return (
    <NavLink
      to={item.path}
      key={item.path}
      className={({ isActive }) =>
        `${s.sidebar_item} ${isActive ? s.active : ""}`
      }
      onClick={onClick}
    >
      {renderContent}
    </NavLink>
  );
};
