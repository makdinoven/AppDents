import s from "./ProfilePage.module.scss";
import { Outlet } from "react-router-dom";
import { ProfileSidebar } from "@/widgets/profile-sidebar/ui/ProfileSidebar.tsx";

const ProfilePage = () => {
  return (
    <div className={s.profile_page_container}>
      <ProfileSidebar />
      <div className={s.profile_content_container}>
        <Outlet />
      </div>
    </div>
  );
};

export default ProfilePage;
