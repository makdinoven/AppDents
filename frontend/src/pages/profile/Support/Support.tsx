import { SupportChatList } from "@/widgets/support/chat-list";
import s from "./Support.module.scss";
import BackButton from "@/shared/components/ui/BackButton/BackButton.tsx";
import { Outlet, useMatch } from "react-router-dom";
import { PATHS } from "@/app/routes/routes.ts";
import { useScreenWidth } from "@/shared/common/hooks/useScreenWidth.ts";
import { ToggleCreateChatButton } from "@/features/support/create-chat";

const Support = () => {
  const screenWidth = useScreenWidth();
  const isMobile = screenWidth < 768;

  const isChatRoute = !!useMatch(PATHS.SUPPORT_CHAT.pattern);
  const isCreateRoute = !!useMatch(PATHS.SUPPORT_CREATE_CHAT);
  const isPanelRoute = isChatRoute || isCreateRoute;

  const showList = !isMobile || !isPanelRoute;
  const showPanel = !isMobile || isPanelRoute;

  return (
    <>
      <BackButton
        link={isMobile && isPanelRoute ? PATHS.SUPPORT : PATHS.PROFILE}
      />

      <div className={s.support_page}>
        <div className={s.support_page_header}>
          <h2>SUPPORT CENTER</h2>

          <ToggleCreateChatButton
            toCreate={PATHS.SUPPORT_CREATE_CHAT}
            toBack={PATHS.SUPPORT}
          />
        </div>

        <div className={s.support_layout_container}>
          {showList && <SupportChatList />}

          {showPanel && (
            <div className={s.chat_section}>
              <Outlet />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Support;
