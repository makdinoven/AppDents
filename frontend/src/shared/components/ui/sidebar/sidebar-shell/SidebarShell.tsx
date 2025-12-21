import s from "./SidebarShell.module.scss";
import { SidebarShellData } from "@/shared/common/types/commonTypes.ts";
import { NavLink } from "react-router-dom";
import { Chevron } from "@/shared/assets/icons";
import { t } from "i18next";

interface SidebarShellProps {
  data: SidebarShellData[];
  onItemClick?: () => void;
}

export const SidebarShell = ({ data, onItemClick }: SidebarShellProps) => {
  return (
    <div className={s.sidebar_shell}>
      {data.map((item) => {
        if (item.type === "custom") {
          return <div key={item.type}>{item.render()}</div>;
        }

        if (item.type === "action") {
          return (
            <button
              key={item.title}
              className={s.sidebar_item}
              onClick={() => {
                item.onClick();
                onItemClick?.();
              }}
            >
              <div className={s.item_content}>
                {item.icon && <span className={s.icon}>{item.icon}</span>}
                <span className={s.title}>{t(item.title)}</span>
              </div>
              <Chevron className={s.arrow} />
            </button>
          );
        }

        return (
          <NavLink
            to={item.path}
            key={item.path}
            className={({ isActive }) =>
              `${s.sidebar_item} ${isActive ? s.active : ""}`
            }
            onClick={onItemClick}
          >
            <div className={s.item_content}>
              {item.icon && <span className={s.icon}>{item.icon}</span>}
              <span className={s.title}>{t(item.title)}</span>
            </div>
            <Chevron className={s.arrow} />
          </NavLink>
        );
      })}
    </div>
  );
};
