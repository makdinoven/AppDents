import { BOOK_LANDING_PATHS, LANDING_PATHS, PATHS } from "./routes";
import MainLayout from "./layouts/MainLayout";
import AdminLayout from "./layouts/AdminLayout";
import ProtectedRoute from "./protected/ProtectedRoute";
import AdminRoute from "./protected/AdminRoute";
import MainPage from "../../pages/MainPage/MainPage";
import Courses from "../../pages/Courses/Courses";
import Books from "../../pages/Books/Books";
import Professors from "../../pages/Professors/Professors";
import ProfessorPage from "../../pages/ProfessorPage/ProfessorPage";
import UniversalPage from "../../pages/UniversalPage/UniversalPage";
import SuccessPayment from "../../pages/SuccessPayment/SuccessPayment";
import Landing from "../../pages/Landing/Landing";
import BookLanding from "../../pages/BookLanding/BookLanding";
import ProfileLayout from "./layouts/ProfileLayout.tsx";
import ProfilePage from "../../pages/ProfilePage/layout/ProfilePage";
import ProfileMain from "../../pages/ProfilePage/pages/ProfileMain/ProfileMain";
import YourCourses from "../../pages/ProfilePage/pages/YourCourses";
import YourBooks from "../../pages/ProfilePage/pages/YourBooks";
import PurchaseHistory from "../../pages/ProfilePage/pages/PurchaseHistory";
import InvitedUsers from "../../pages/ProfilePage/pages/InvitedUsers";
import CoursePage from "../../pages/ProfilePage/pages/CoursePage/CoursePage";
import LessonPage from "../../pages/ProfilePage/pages/LessonPage/LessonPage";
import BookPage from "../../pages/ProfilePage/pages/BookPage/BookPage";
import AdminPage from "../../pages/Admin/AdminPage";
import AdminCoursesListing from "../../pages/Admin/pages/content/AdminCoursesListing";
import AdminLandingsListing from "../../pages/Admin/pages/content/AdminLandingsListing";
import AdminAuthorsListing from "../../pages/Admin/pages/content/AdminAuthorsListing";
import AdminUsersListing from "../../pages/Admin/pages/content/AdminUsersListing";
import AdminBooksListing from "../../pages/Admin/pages/content/AdminBooksListing";
import AdminBookLandingsListing from "../../pages/Admin/pages/content/AdminBookLandingsListing";
import AnalyticsPurchases from "../../pages/Admin/pages/analytics/AnalyticsPurchases";
import AnalyticsLanguageStats from "../../pages/Admin/pages/analytics/AnalyticsLanguageStats";
import AnalyticsAdListing from "../../pages/Admin/pages/analytics/AnalyticsAdListing";
import AnalyticsReferrals from "../../pages/Admin/pages/analytics/AnalyticsReferrals";
import AnalyticsUserGrowth from "../../pages/Admin/pages/analytics/AnalyticsUserGrowth";
import AnalyticsFreewebs from "../../pages/Admin/pages/analytics/AnalyticsFreewebs";
import AnalyticsTraffic from "../../pages/Admin/pages/analytics/AnalyticsTraffic";
import NotFoundPage from "../../pages/NotFoundPage/NotFoundPage";
import ClipTool from "../../pages/Admin/pages/tools/ClipTool/ClipTool.tsx";
import MagicVideoTool from "../../pages/Admin/pages/tools/MagicVideoTool/MagicVideoTool.tsx";
import VideoSummaryTool from "../../pages/Admin/pages/tools/VideoSummaryTool/VideoSummaryTool.tsx";
import BookLandingAnalytics from "../../pages/Admin/pages/analytics/LandingAnalytics/BookLandingAnalytics.tsx";
import LandingAnalytics from "../../pages/Admin/pages/analytics/LandingAnalytics/LandingAnalytics.tsx";
import AdControlStaff from "../../pages/Admin/pages/ad-control/AdControlStaff.tsx";
import AdControlListing from "../../pages/Admin/pages/ad-control/AdControlListing/AdControlListing.tsx";
import AdControlAccounts from "../../pages/Admin/pages/ad-control/AdControlAccounts.tsx";
import CourseDetail from "../../pages/Admin/pages/detail/CourseDetail.tsx";
import LandingDetail from "../../pages/Admin/pages/detail/LandingDetail.tsx";
import AuthorDetail from "../../pages/Admin/pages/detail/AuthorDetail.tsx";
import BookLandingDetail from "../../pages/Admin/pages/detail/BookLandingDetail..tsx";
import UserDetail from "../../pages/Admin/pages/detail/UserDetail.tsx";
import BookDetail from "../../pages/Admin/pages/detail/BookDetail/BookDetail.tsx";
import { AUTH_MODAL_ROUTES } from "../../shared/common/helpers/commonConstants.ts";

export const routesConfig = (hasBg: boolean) => [
  {
    path: PATHS.MAIN,
    element: <MainLayout />,
    children: [
      { index: true, element: <MainPage /> },
      ...AUTH_MODAL_ROUTES.map((p) => ({
        path: p,
        element: <MainPage />,
      })),
      !hasBg && {
        path: PATHS.CART,
        element: <MainPage />,
      },
      !hasBg && {
        path: PATHS.SEARCH,
        element: <MainPage />,
      },

      {
        path: PATHS.COURSES_LISTING,
        element: <Courses isFree={false} />,
      },
      { path: PATHS.COURSES_LISTING_FREE, element: <Courses isFree /> },
      { path: PATHS.BOOKS_LISTING, element: <Books /> },
      ...LANDING_PATHS.map((p) => ({
        path: p.pattern,
        element: <Landing />,
      })),
      ...BOOK_LANDING_PATHS.map((p) => ({
        path: p.pattern,
        element: <BookLanding />,
      })),
      { path: PATHS.SUCCESS_PAYMENT, element: <SuccessPayment /> },
      { path: PATHS.PROFESSORS_LISTING, element: <Professors /> },
      { path: PATHS.PROFESSOR_PAGE.pattern, element: <ProfessorPage /> },
      { path: PATHS.INFO.pattern, element: <UniversalPage /> },

      {
        element: (
          <ProtectedRoute>
            <ProfileLayout />
          </ProtectedRoute>
        ),
        children: [
          {
            element: <ProfilePage />,
            children: [
              { path: PATHS.PROFILE, element: <ProfileMain /> },
              { path: PATHS.PROFILE_MY_COURSES, element: <YourCourses /> },
              { path: PATHS.PROFILE_MY_BOOKS, element: <YourBooks /> },
              {
                path: PATHS.PROFILE_PURCHASE_HISTORY,
                element: <PurchaseHistory />,
              },
              {
                path: PATHS.PROFILE_INVITED_USERS,
                element: <InvitedUsers />,
              },
            ],
          },

          {
            path: PATHS.PROFILE_MY_COURSE.pattern,
            element: <CoursePage />,
            children: [
              {
                path: PATHS.PROFILE_COURSE_LESSON.pattern,
                element: <LessonPage />,
              },
            ],
          },
          {
            path: PATHS.PROFILE_MY_BOOK.pattern,
            element: <BookPage />,
          },
        ],
      },
    ],
  },

  {
    path: PATHS.ADMIN,
    element: (
      <ProtectedRoute>
        <AdminRoute>
          <AdminLayout />
        </AdminRoute>
      </ProtectedRoute>
    ),
    children: [
      {
        element: <AdminPage />,
        children: [
          {
            path: PATHS.ADMIN_COURSES_LISTING,
            element: <AdminCoursesListing />,
          },
          {
            path: PATHS.ADMIN_LANDINGS_LISTING,
            element: <AdminLandingsListing />,
          },
          {
            path: PATHS.ADMIN_AUTHORS_LISTING,
            element: <AdminAuthorsListing />,
          },
          {
            path: PATHS.ADMIN_BOOK_LANDING_ANALYTICS.pattern,
            element: <BookLandingAnalytics />,
          },
          {
            path: PATHS.ADMIN_LANDING_ANALYTICS.pattern,
            element: <LandingAnalytics />,
          },
          {
            path: PATHS.ADMIN_USERS_LISTING,
            element: <AdminUsersListing />,
          },
          {
            path: PATHS.ADMIN_BOOKS_LISTING,
            element: <AdminBooksListing />,
          },
          {
            path: PATHS.ADMIN_BOOK_LANDINGS_LISTING,
            element: <AdminBookLandingsListing />,
          },

          {
            path: PATHS.ADMIN_COURSE_DETAIL.pattern,
            element: <CourseDetail />,
          },
          {
            path: PATHS.ADMIN_LANDING_DETAIL.pattern,
            element: <LandingDetail />,
          },
          {
            path: PATHS.ADMIN_AUTHOR_DETAIL.pattern,
            element: <AuthorDetail />,
          },
          {
            path: PATHS.ADMIN_BOOK_LANDING_DETAIL.pattern,
            element: <BookLandingDetail />,
          },
          {
            path: PATHS.ADMIN_USER_DETAIL.pattern,
            element: <UserDetail />,
          },
          {
            path: PATHS.ADMIN_BOOK_DETAIL.pattern,
            element: <BookDetail />,
          },

          {
            path: PATHS.ADMIN_LANDING_ANALYTICS.pattern,
            element: <LandingAnalytics />,
          },
          {
            path: PATHS.ADMIN_BOOK_LANDING_ANALYTICS.pattern,
            element: <BookLandingAnalytics />,
          },

          {
            path: PATHS.ADMIN_ANALYTICS_PURCHASES,
            element: <AnalyticsPurchases />,
          },
          {
            path: PATHS.ADMIN_ANALYTICS_LANG_STATS,
            element: <AnalyticsLanguageStats />,
          },
          {
            path: PATHS.ADMIN_ANALYTICS_AD_LISTING,
            element: <AnalyticsAdListing />,
          },
          {
            path: PATHS.ADMIN_ANALYTICS_REFERRALS,
            element: <AnalyticsReferrals />,
          },
          {
            path: PATHS.ADMIN_ANALYTICS_USER_GROWTH,
            element: <AnalyticsUserGrowth />,
          },
          {
            path: PATHS.ADMIN_ANALYTICS_FREEWEBS,
            element: <AnalyticsFreewebs />,
          },
          {
            path: PATHS.ADMIN_ANALYTICS_TRAFFIC,
            element: <AnalyticsTraffic />,
          },

          {
            path: PATHS.ADMIN_AD_CONTROL_STAFF,
            element: <AdControlStaff />,
          },
          {
            path: PATHS.ADMIN_AD_CONTOL_LISTING,
            element: <AdControlListing />,
          },
          {
            path: PATHS.ADMIN_AD_CONTROL_ACCOUNTS,
            element: <AdControlAccounts />,
          },

          { path: PATHS.ADMIN_TOOLS_CLIP, element: <ClipTool /> },
          { path: PATHS.ADMIN_TOOLS_MAGIC, element: <MagicVideoTool /> },
          {
            path: PATHS.ADMIN_TOOLS_VIDEO_SUMMARY,
            element: <VideoSummaryTool />,
          },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
];
