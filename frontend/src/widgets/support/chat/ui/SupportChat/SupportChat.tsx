import s from "./SupportChat.module.scss";

export const SupportChat = ({ chatId }: { chatId: string }) => {
  return <div className={s.chat_container}>chat {chatId}</div>;
};
