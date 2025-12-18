import s from "./ProfilePage.module.scss";
import { Outlet } from "react-router-dom";
import { ProfileSidebar } from "@/widgets/ProfileSidebar/ui/ProfileSidebar.tsx";

const ProfilePage = () => {
  return (
    <div className={s.profile_page_container}>
      <ProfileSidebar />
      <Outlet />
    </div>
  );
};

export default ProfilePage;
