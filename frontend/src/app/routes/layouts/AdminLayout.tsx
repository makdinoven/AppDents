import Header from "../../../shared/components/Header/Header.tsx";
import s from "./Layout.module.scss";
import { Outlet } from "react-router-dom";

const AdminLayout = () => {
  return (
    <div className={s.main_wrapper}>
      <Header />
      <main className={s.content}>
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
