import { useDispatch, useSelector } from "react-redux";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../shared/store/store.ts";
import {
  createCourse,
  getCourses,
  searchCourses,
} from "../../../../shared/store/actions/adminActions.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { INITIAL_COURSE } from "../../../../shared/common/helpers/commonConstants.ts";
import { PATHS } from "../../../../app/routes/routes.ts";

const AdminCoursesListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const courses = useSelector((state: AppRootStateType) => state.admin.courses);
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        transKey={"courses"}
        data={courses}
        itemName={"name"}
        itemLink={(course) => PATHS.ADMIN_COURSE_DETAIL.build(course.id)}
        loading={loading}
        onSearch={(params) => dispatch(searchCourses(params))}
        onLoad={(params) => dispatch(getCourses(params))}
        onCreate={() => dispatch(createCourse(INITIAL_COURSE))}
      />
    </>
  );
};

export default AdminCoursesListing;
