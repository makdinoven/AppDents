import s from "./AdminSidebar.module.scss";
import { BackArrow } from "../../../shared/assets/icons";
import { NavLink } from "react-router-dom";
import { useScreenWidth } from "../../../shared/common/hooks/useScreenWidth.ts";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../../shared/common/hooks/useOutsideClick.ts";
import { Trans } from "react-i18next";

const AdminSidebar = ({
  isMinimized,
  links,
  setIsMinimized,
}: {
  links: { label: string; innerLinks: { label: string; link: string }[] }[];
  isMinimized: boolean;
  setIsMinimized: (val: boolean) => void;
}) => {
  const screenWidth = useScreenWidth();
  const sidebarRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const renderMobile = screenWidth <= 1024;
  useOutsideClick(sidebarRef, () => setIsOpen(false));

  const handleCloseSidebar = () => {
    setIsOpen(false);
  };

  useEffect(() => {
    if (renderMobile && isOpen) {
      setIsMinimized(false);
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = "";
      };
    }
  }, [isOpen, renderMobile]);

  return (
    <>
      <button
        className={`${s.burger_btn} ${isMinimized || (renderMobile && !isOpen) ? s.visible : ""}`}
        onClick={() => (renderMobile ? setIsOpen(true) : setIsMinimized(false))}
      >
        <span />
        <span />
        <span />
      </button>

      <div
        ref={sidebarRef}
        className={`${s.sidebar} ${renderMobile ? s.mobile : ""} ${renderMobile && isOpen ? s.open : ""} ${isMinimized ? s.minimized : ""}`}
      >
        <button
          className={s.close_btn}
          onClick={() =>
            renderMobile ? handleCloseSidebar() : setIsMinimized(true)
          }
        >
          <span></span>
          <span></span>
        </button>

        <ul className={s.outer_list}>
          {links.map((item) => (
            <li className={s.outer_list_section} key={item.label}>
              <span className={s.outer_list_item}>
                <Trans i18nKey={item.label} />
              </span>
              {item.innerLinks && (
                <ul className={s.inner_list}>
                  {item.innerLinks.map((link) => (
                    <li key={link.label}>
                      <NavLink
                        to={link.link}
                        onClick={renderMobile ? handleCloseSidebar : undefined}
                        className={({ isActive }) =>
                          `${s.inner_list_item} ${isActive ? s.active : ""}`
                        }
                      >
                        <Trans i18nKey={link.label} />
                        <BackArrow className={s.arrow} />
                      </NavLink>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      </div>
    </>
  );
};

export default AdminSidebar;
