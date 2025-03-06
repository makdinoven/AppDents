import MainPage from "../pages/MainPage/MainPage.tsx";
import Layout from "../components/Layout/Layout.tsx";
import Landing from "../pages/Landing/Landing.tsx";
import PersonalAccount from "../pages/PersonalAccount/PersonalAccount.tsx";
import { Path } from "./routes.ts";
import { FC } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AdminPanel from "../pages/Admin/AdminPanel/AdminPanel.tsx";
import CourseDetail from "../pages/Admin/modules/CourseDetail/CourseDetail.tsx";
import AdminPage from "../pages/Admin/AdminPage.tsx";
import LandingDetail from "../pages/Admin/modules/LandingDetail/LandingDetail.tsx";

export const AppRoutes: FC = () => {
  return (
    <Routes>
      <Route path={Path.main} element={<Layout />}>
        <Route path=":modalType?" element={<MainPage />} />
        <Route
          path={`${Path.landing}/:landingPath?/:modalType?`}
          element={<Landing />}
        />
        <Route path={Path.profile} element={<PersonalAccount />} />

        <Route path={Path.admin} element={<AdminPage />}>
          <Route index element={<AdminPanel />} />
          <Route
            path={`${Path.courseDetail}/:courseId?`}
            element={<CourseDetail />}
          />
          <Route
            path={`${Path.landingDetail}/:landingId?`}
            element={<LandingDetail />}
          />
          {/*<Route path="*" element={<Navigate to={Path.admin} replace />} />*/}
        </Route>

        <Route path="*" element={<Navigate to={Path.main} replace />} />
      </Route>
    </Routes>
  );
};
