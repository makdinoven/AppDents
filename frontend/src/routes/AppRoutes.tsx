import MainPage from "../pages/MainPage/MainPage.tsx";
import Layout from "../components/Layout/Layout.tsx";
import Landing from "../pages/Landing/Landing.tsx";
import ProfileMain from "../pages/ProfilePage/pages/ProfileMain/content/Main/ProfileMain.tsx";
import { Path } from "./routes.ts";
import { FC } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import CourseDetail from "../pages/Admin/pages/detail/CourseDetail.tsx";
import AdminPage from "../pages/Admin/AdminPage.tsx";
import LandingDetail from "../pages/Admin/pages/detail/LandingDetail.tsx";
import AuthorDetail from "../pages/Admin/pages/detail/AuthorDetail.tsx";
import CoursePage from "../pages/ProfilePage/pages/CoursePage/CoursePage.tsx";
import SuccessPayment from "../pages/SuccessPayment/SuccessPayment.tsx";
import LessonPage from "../pages/ProfilePage/pages/LessonPage/LessonPage.tsx";
import UserDetail from "../pages/Admin/pages/detail/UserDetail.tsx";
import ProfilePage from "../pages/ProfilePage/layout/ProfilePage.tsx";
import ProfessorPage from "../pages/ProfessorPage/ProfessorPage.tsx";
import UniversalPage from "../pages/UniversalPage/UniversalPage.tsx";
import Professors from "../pages/Professors/Professors.tsx";
import NotFoundPage from "../pages/NotFoundPage/NotFoundPage.tsx";
import AuthModalManager from "../components/AuthModalManager/AuthModalManager.tsx";
import {
  AUTH_MODAL_ROUTES,
  BOOK_LANDING_ROUTES,
  LANDING_ROUTES,
} from "../common/helpers/commonConstants.ts";
import ProtectedRoute from "./protected/ProtectedRoute.tsx";
import AdminRoute from "./protected/AdminRoute.tsx";
import Cart from "../pages/Cart/Cart.tsx";
import Courses from "../pages/Courses/Courses.tsx";
import BookLanding from "../pages/BookLanding/BookLanding.tsx";
import Books from "../pages/Books/Books.tsx";
import SearchPage from "../pages/SearchPage/SearchPage.tsx";
import BookLandingDetail from "../pages/Admin/pages/detail/BookLandingDetail..tsx";
import BookDetail from "../pages/Admin/pages/detail/BookDetail/BookDetail.tsx";
import LandingAnalytics from "../pages/Admin/pages/analytics/LandingAnalytics/LandingAnalytics.tsx";
import AnalyticsPurchases from "../pages/Admin/pages/analytics/AnalyticsPurchases.tsx";
import AnalyticsLanguageStats from "../pages/Admin/pages/analytics/AnalyticsLanguageStats.tsx";
import AnalyticsAdListing from "../pages/Admin/pages/analytics/AnalyticsAdListing.tsx";
import AnalyticsReferrals from "../pages/Admin/pages/analytics/AnalyticsReferrals.tsx";
import AnalyticsUserGrowth from "../pages/Admin/pages/analytics/AnalyticsUserGrowth.tsx";
import AnalyticsFreewebs from "../pages/Admin/pages/analytics/AnalyticsFreewebs.tsx";
import AnalyticsTraffic from "../pages/Admin/pages/analytics/AnalyticsTraffic.tsx";
import VideoSummaryTool from "../pages/Admin/pages/tools/VideoSummaryTool/VideoSummaryTool.tsx";
import ClipTool from "../pages/Admin/pages/tools/ClipTool/ClipTool.tsx";
import AdControlStaff from "../pages/Admin/pages/ad-control/AdControlStaff.tsx";
import AdControlAccounts from "../pages/Admin/pages/ad-control/AdControlAccounts.tsx";
import AdControlListing from "../pages/Admin/pages/ad-control/AdControlListing/AdControlListing.tsx";
import AdminLandingsListing from "../pages/Admin/pages/content/AdminLandingsListing.tsx";
import AdminCoursesListing from "../pages/Admin/pages/content/AdminCoursesListing.tsx";
import AdminAuthorsListing from "../pages/Admin/pages/content/AdminAuthorsListing.tsx";
import AdminUsersListing from "../pages/Admin/pages/content/AdminUsersListing.tsx";
import AdminBooksListing from "../pages/Admin/pages/content/AdminBooksListing.tsx";
import AdminBookLandingsListing from "../pages/Admin/pages/content/AdminBookLandingsListing.tsx";
import BookPage from "../pages/ProfilePage/pages/BookPage/BookPage.tsx";
import MagicVideoTool from "../pages/Admin/pages/tools/MagicVideoTool/MagicVideoTool.tsx";
import BookLandingAnalytics from "../pages/Admin/pages/analytics/LandingAnalytics/BookLandingAnalytics.tsx";
import PurchaseHistory from "../pages/ProfilePage/pages/ProfileMain/content/PurchaseHistory/PurchaseHistory.tsx";
import YourBooks from "../pages/ProfilePage/pages/YourBooks.tsx";
import YourCourses from "../pages/ProfilePage/pages/YourCourses.tsx";

export const AppRoutes: FC = () => {
  const location = useLocation();
  const backgroundLocation = location.state?.backgroundLocation || null;
  const isAuthModalRoute = AUTH_MODAL_ROUTES.includes(location.pathname);
  const isCartPage = location.pathname === Path.cart;
  const isSearchPage = location.pathname === Path.search;

  return (
    <>
      <Routes location={backgroundLocation || location}>
        <Route path={Path.main} element={<Layout />}>
          {AUTH_MODAL_ROUTES.map((path) => (
            <Route key={path} path={path} element={<MainPage />} />
          ))}
          {!backgroundLocation && (
            <>
              <Route path={Path.cart} element={<MainPage />} />
              <Route path={Path.search} element={<MainPage />} />
            </>
          )}

          <Route path={Path.courses} element={<Courses isFree={false} />} />
          <Route path={Path.books} element={<Books />} />
          <Route path={Path.freeCourses} element={<Courses isFree={true} />} />
          <Route index element={<MainPage />} />

          {BOOK_LANDING_ROUTES.map((path) => (
            <Route
              key={path}
              path={`${path}/:landingPath?`}
              element={<BookLanding />}
            />
          ))}

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
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          >
            <Route path={Path.profileMain} element={<ProfileMain />} />
            <Route path={Path.yourCourses} element={<YourCourses />} />
            <Route path={Path.yourBooks} element={<YourBooks />} />
            <Route path={Path.purchaseHistory} element={<PurchaseHistory />} />
            <Route
              path={`${Path.myCourse}/:courseId?`}
              element={<CoursePage />}
            >
              <Route
                path={`${Path.lesson}/:sectionId/:lessonId`}
                element={<LessonPage />}
              />
            </Route>
            <Route path={`${Path.myBook}/:bookId?`} element={<BookPage />} />
          </Route>

          <Route
            path={Path.admin}
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          >
            <Route
              path={`${Path.adminLandingListing}`}
              element={<AdminLandingsListing />}
            />
            <Route
              path={`${Path.adminCourseListing}`}
              element={<AdminCoursesListing />}
            />
            <Route
              path={`${Path.adminAuthorListing}`}
              element={<AdminAuthorsListing />}
            />
            <Route
              path={`${Path.adminUserListing}`}
              element={<AdminUsersListing />}
            />
            <Route
              path={`${Path.adminBookListing}`}
              element={<AdminBooksListing />}
            />
            <Route
              path={`${Path.adminBookLandingListing}`}
              element={<AdminBookLandingsListing />}
            />
            <Route
              path={`${Path.adminPurchases}`}
              element={<AnalyticsPurchases />}
            />
            <Route
              path={`${Path.adminLanguageStats}`}
              element={<AnalyticsLanguageStats />}
            />
            <Route
              path={`${Path.adminAdListing}`}
              element={<AnalyticsAdListing />}
            />
            <Route
              path={`${Path.adminReferrals}`}
              element={<AnalyticsReferrals />}
            />
            <Route
              path={`${Path.adminUserGrowth}`}
              element={<AnalyticsUserGrowth />}
            />
            <Route
              path={`${Path.adminFreewebs}`}
              element={<AnalyticsFreewebs />}
            />
            <Route
              path={`${Path.adminTraffic}`}
              element={<AnalyticsTraffic />}
            />
            <Route
              path={`${Path.adminAdControlListing}`}
              element={<AdControlListing />}
            />
            <Route
              path={`${Path.adminAdControlStaff}`}
              element={<AdControlStaff />}
            />
            <Route
              path={`${Path.adminAdControlAccounts}`}
              element={<AdControlAccounts />}
            />

            <Route
              path={`${Path.adminVideoSummaryTool}`}
              element={<VideoSummaryTool />}
            />
            <Route path={`${Path.adminClipTool}`} element={<ClipTool />} />
            <Route
              path={`${Path.adminMagicVideoTool}`}
              element={<MagicVideoTool />}
            />

            <Route
              path={`${Path.courseDetail}/:courseId?`}
              element={<CourseDetail />}
            />
            <Route
              path={`${Path.landingAnalytics}/:landingId?`}
              element={<LandingAnalytics />}
            />
            <Route
              path={`${Path.bookLandingAnalytics}/:landingId?`}
              element={<BookLandingAnalytics />}
            />
            <Route
              path={`${Path.landingDetail}/:landingId?`}
              element={<LandingDetail />}
            />
            <Route
              path={`${Path.bookLandingDetail}/:bookId?`}
              element={<BookLandingDetail />}
            />
            <Route
              path={`${Path.bookDetail}/:bookId?`}
              element={<BookDetail />}
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

      {(backgroundLocation || isAuthModalRoute) && <AuthModalManager />}
      {isCartPage && <Cart />}
      {isSearchPage && <SearchPage />}
    </>
  );
};
