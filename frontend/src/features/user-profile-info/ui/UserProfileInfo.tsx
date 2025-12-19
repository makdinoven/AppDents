import s from "./UserProfileInfo.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";
import { UserFilled } from "@/shared/assets/icons";

export const UserProfileInfo = () => {
  const email = useSelector((state: AppRootStateType) => state.user.email);

  return (
    <div className={s.user_profile_info}>
      <UserFilled />
      <span>{email}</span>
    </div>
  );
};
