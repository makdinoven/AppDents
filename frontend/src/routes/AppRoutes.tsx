import MainPage from "../pages/MainPage/MainPage.tsx";
import Layout from "../components/Layout/Layout.tsx";
import Landing from "../pages/Landing/Landing.tsx";
import ProfileMain from "../pages/ProfilePage/pages/ProfileMain/ProfileMain.tsx";
import { Path } from "./routes.ts";
import { FC } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AdminPanel from "../pages/Admin/AdminPanel/AdminPanel.tsx";
import CourseDetail from "../pages/Admin/pages/CourseDetail.tsx";
import AdminPage from "../pages/Admin/AdminPage.tsx";
import LandingDetail from "../pages/Admin/pages/LandingDetail.tsx";
import AuthorDetail from "../pages/Admin/pages/AuthorDetail.tsx";
import CoursePage from "../pages/ProfilePage/pages/CoursePage/CoursePage.tsx";
import SuccessPayment from "../pages/SuccessPayment/SuccessPayment.tsx";
import LessonPage from "../pages/ProfilePage/pages/LessonPage/LessonPage.tsx";
import UserDetail from "../pages/Admin/pages/UserDetail.tsx";
import ProfilePage from "../pages/ProfilePage/ProfilePage.tsx";

export const AppRoutes: FC = () => {
  return (
    <Routes>
      <Route path={Path.main} element={<Layout />}>
        <Route path=":modalType?" element={<MainPage />} />
        <Route
          path={`${Path.landing}/:landingPath?/:modalType?`}
          element={<Landing />}
        />
        <Route path={Path.successPayment} element={<SuccessPayment />} />

        <Route path={Path.profile} element={<ProfilePage />}>
          <Route index element={<ProfileMain />} />
          <Route path={`${Path.myCourse}/:courseId?`} element={<CoursePage />}>
            <Route
              path={`${Path.lesson}/:sectionId/:lessonId`}
              element={<LessonPage />}
            />
          </Route>
        </Route>

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
          <Route
            path={`${Path.userDetail}/:userId?`}
            element={<UserDetail />}
          />
          {/*<Route path="*" element={<Navigate to={Path.admin} replace />} />*/}
        </Route>

        <Route path="*" element={<Navigate to={Path.main} replace />} />
      </Route>
    </Routes>
  );
};
