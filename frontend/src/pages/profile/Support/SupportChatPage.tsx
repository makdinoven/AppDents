import { useParams } from "react-router-dom";
import { SupportChat } from "@/widgets/support/chat";

export const SupportChatPage = () => {
  const { id } = useParams();

  if (!id) return null;

  return <SupportChat key={id} chatId={id} />;
};
