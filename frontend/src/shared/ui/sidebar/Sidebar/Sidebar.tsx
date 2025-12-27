import s from "./Sidebar.module.scss";
import { RemoveScroll } from "react-remove-scroll";
import { ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { SidebarTrigger } from "@/shared/ui/sidebar/SidebarTrigger/SidebarTrigger";
import useOutsideClickMulti from "@/shared/common/hooks/useOutsideClickMulti";
import Button from "@/shared/components/ui/Button/Button";
import { SidebarClose, SidebarOpen } from "@/shared/assets/icons";
import { useScreenWidth } from "@/shared/common/hooks/useScreenWidth";

type SidebarCtx = {
  isCollapsed: boolean;
  toggleCollapsed: () => void;
};

type SidebarSection<TItem> =
  | TItem[]
  | {
      title?: ReactNode;
      items: TItem[];
    };

interface SidebarProps<TItem> {
  menuButtonText?: string;
  menuButtonClassName?: string;
  sections: SidebarSection<TItem>[];
  topSlot?: ReactNode;
  bottomSlot?: ReactNode;
  renderItem: (item: TItem, close: () => void, ctx: SidebarCtx) => ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  persistKey?: string;
  showCollapseButton?: boolean;
  autoCollapse?: boolean;
  autoCollapseKey?: string | number;
  renderSectionTitle?: (title: ReactNode, ctx: SidebarCtx) => ReactNode;
}

const readPersisted = (key: string): boolean | null => {
  const v = localStorage.getItem(key);
  if (v === "1") return true;
  if (v === "0") return false;
  return null;
};

export const Sidebar = <TItem,>({
  menuButtonText,
  menuButtonClassName,
  sections,
  topSlot,
  bottomSlot,
  renderItem,
  collapsible = true,
  defaultCollapsed = false,
  persistKey = "ui.sidebar.collapsed",
  showCollapseButton = true,
  renderSectionTitle,
}: SidebarProps<TItem>) => {
  const [isOpen, setIsOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const screenWidth = useScreenWidth();
  const isMobile = screenWidth < 768;

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    const persisted = readPersisted(persistKey);
    return persisted ?? defaultCollapsed;
  });

  const effectiveCollapsed = isMobile ? false : collapsed;

  useEffect(() => {
    if (isMobile) return;
    try {
      localStorage.setItem(persistKey, collapsed ? "1" : "0");
    } catch {}
  }, [persistKey, collapsed, isMobile]);

  const toggleCollapsed = () => {
    if (!collapsible) return;
    if (isMobile) return;
    setCollapsed((v) => !v);
  };

  const handleSidebarClose = () => setIsOpen(false);
  const toggleSidebar = () => setIsOpen((prev) => !prev);

  useOutsideClickMulti([sidebarRef, triggerRef], () => {
    if (isOpen) handleSidebarClose();
  });

  const ctx = useMemo<SidebarCtx>(
    () => ({ isCollapsed: effectiveCollapsed, toggleCollapsed }),
    [effectiveCollapsed],
  );

  const normalizedSections = useMemo(() => {
    return sections.map((sec) => {
      if (Array.isArray(sec)) return { title: null as ReactNode, items: sec };
      return { title: sec.title ?? null, items: sec.items };
    });
  }, [sections]);

  return (
    <>
      <SidebarTrigger
        ref={triggerRef}
        isOpen={isOpen}
        text={menuButtonText}
        className={menuButtonClassName}
        onClick={toggleSidebar}
      />

      <RemoveScroll enabled={isOpen}>
        <div
          className={s.sidebar_wrapper}
          ref={sidebarRef}
          data-open={isOpen ? "1" : "0"}
          data-collapsed={effectiveCollapsed ? "1" : "0"}
          data-mobile={isMobile ? "1" : "0"}
        >
          <div className={`${s.sidebar} ${isOpen ? s.open : ""}`}>
            <div className={s.sidebar_header}>
              {topSlot && !effectiveCollapsed && topSlot}

              {collapsible && showCollapseButton && !isMobile && (
                <Button
                  type="button"
                  variant="outlined"
                  className={`${s.collapseBtn} ${
                    effectiveCollapsed ? s.centered : ""
                  }`}
                  onClick={toggleCollapsed}
                >
                  {effectiveCollapsed ? <SidebarOpen /> : <SidebarClose />}
                </Button>
              )}
            </div>

            {normalizedSections.map((section, i) => (
              <div key={i} className={s.sidebar_section_wrapper}>
                {section.title && !effectiveCollapsed && (
                  <div className={s.section_title}>
                    {renderSectionTitle
                      ? renderSectionTitle(section.title, ctx)
                      : section.title}
                  </div>
                )}

                <div className={s.sidebar_section}>
                  {section.items.map((item) =>
                    renderItem(item, handleSidebarClose, ctx),
                  )}
                </div>
              </div>
            ))}

            {bottomSlot && !effectiveCollapsed && bottomSlot}
          </div>
        </div>
      </RemoveScroll>
    </>
  );
};
