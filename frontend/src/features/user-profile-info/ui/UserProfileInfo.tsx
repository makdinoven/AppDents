import s from "./UserProfileInfo.module.scss";
import { useSelector } from "react-redux";
import { UserFilled } from "@/shared/assets/icons";
import { AppRootStateType } from "@/shared/store/store";

export const UserProfileInfo = () => {
  const email = useSelector((state: AppRootStateType) => state.user.email);

  return (
    <div className={s.user_profile_info}>
      <UserFilled />
      <span>{email}</span>
    </div>
  );
};
