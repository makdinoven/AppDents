import MainPage from "../pages/MainPage/MainPage.tsx";
import Layout from "../components/Layout/Layout.tsx";
import Landing from "../pages/Landing/Landing.tsx";
import ProfilePage from "../pages/ProfilePage/ProfilePage.tsx";
import { Path } from "./routes.ts";
import { FC } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AdminPanel from "../pages/Admin/AdminPanel/AdminPanel.tsx";
import CourseDetail from "../pages/Admin/pages/CourseDetail.tsx";
import AdminPage from "../pages/Admin/AdminPage.tsx";
import LandingDetail from "../pages/Admin/pages/LandingDetail.tsx";
import AuthorDetail from "../pages/Admin/pages/AuthorDetail.tsx";

export const AppRoutes: FC = () => {
  return (
    <Routes>
      <Route path={Path.main} element={<Layout />}>
        <Route path=":modalType?" element={<MainPage />} />
        <Route
          path={`${Path.landing}/:landingPath?/:modalType?`}
          element={<Landing />}
        />
        <Route path={Path.profile} element={<ProfilePage />} />

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
          <Route
            path={`${Path.authorDetail}/:authorId?`}
            element={<AuthorDetail />}
          />
          {/*<Route*/}
          {/*    path={`${Path.userDetail}/:landingId?`}*/}
          {/*    element={<UserDetail />}*/}
          {/*/>*/}
          {/*<Route path="*" element={<Navigate to={Path.admin} replace />} />*/}
        </Route>

        <Route path="*" element={<Navigate to={Path.main} replace />} />
      </Route>
    </Routes>
  );
};
