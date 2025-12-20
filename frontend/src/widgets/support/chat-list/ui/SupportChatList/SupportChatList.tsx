import s from "./SupportChatList.module.scss";
import { Link } from "react-router-dom";
import { PATHS } from "@/app/routes/routes.ts";

export const SupportChatList = () => {
  return (
    <div className={s.list_container}>
      <Link to={PATHS.SUPPORT_CHAT.build("123")}>chat link</Link>
      <Link to={PATHS.SUPPORT_CHAT.build("122223")}>chat link2</Link>
    </div>
  );
};
