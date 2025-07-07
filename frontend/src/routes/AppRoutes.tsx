import MainPage from "../pages/MainPage/MainPage.tsx";
import Layout from "../components/Layout/Layout.tsx";
import Landing from "../pages/Landing/Landing.tsx";
import ProfileMain from "../pages/ProfilePage/pages/ProfileMain/ProfileMain.tsx";
import { Path } from "./routes.ts";
import { FC } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
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
import ProfessorPage from "../pages/ProfessorPage/ProfessorPage.tsx";
import UniversalPage from "../pages/UniversalPage/UniversalPage.tsx";
import Professors from "../pages/Professors/Professors.tsx";
import NotFoundPage from "../pages/NotFoundPage/NotFoundPage.tsx";
import AuthModalManager from "../components/AuthModalManager/AuthModalManager.tsx";
import {
  AUTH_MODAL_ROUTES,
  LANDING_ROUTES,
} from "../common/helpers/commonConstants.ts";
import ProtectedRoute from "./protected/ProtectedRoute.tsx";
import AdminRoute from "./protected/AdminRoute.tsx";
import Cart from "../pages/Cart/Cart.tsx";
import Courses from "../pages/Courses/Courses.tsx";
import PaymentPage from "../pages/PaymentPage/PaymentPage.tsx";

export const AppRoutes: FC = () => {
  const location = useLocation();
  const backgroundLocation = location.state?.backgroundLocation || null;
  const isModalRoute = AUTH_MODAL_ROUTES.includes(location.pathname);

  return (
    <>
      <Routes location={backgroundLocation || location}>
        <Route path={Path.main} element={<Layout />}>
          {AUTH_MODAL_ROUTES.map((path) => (
            <Route key={path} path={path} element={<MainPage />} />
          ))}
          <Route path={Path.cart} element={<MainPage />} />
          <Route path={Path.courses} element={<Courses isFree={false} />} />
          <Route path={Path.freeCourses} element={<Courses isFree={true} />} />
          <Route index element={<MainPage />} />

          {LANDING_ROUTES.map((path) => (
            <Route
              key={path}
              path={`${path}/:landingPath?`}
              element={<Landing />}
            />
          ))}
          <Route path={Path.successPayment} element={<SuccessPayment />} />
          <Route
            path={`${Path.professor}/:professorId`}
            element={<ProfessorPage />}
          />
          <Route path={`${Path.professors}`} element={<Professors />} />
          <Route path={`${Path.info}/:pageType`} element={<UniversalPage />} />

          <Route
            path={Path.profile}
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          >
            <Route index element={<ProfileMain />} />
            <Route
              path={`${Path.myCourse}/:courseId?`}
              element={<CoursePage />}
            >
              <Route
                path={`${Path.lesson}/:sectionId/:lessonId`}
                element={<LessonPage />}
              />
            </Route>
          </Route>

          <Route
            path={Path.admin}
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          >
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
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>

      {(backgroundLocation || isModalRoute) && <AuthModalManager />}
      {location.pathname === Path.cart && <Cart />}

      {location.pathname.startsWith(Path.payment) && (
        <Routes>
          <Route path={`${Path.payment}/:slug`} element={<PaymentPage />} />
        </Routes>
      )}
    </>
  );
};
