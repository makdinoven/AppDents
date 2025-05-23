import { useDispatch, useSelector } from "react-redux";
import {
  createCourse,
  getCourses,
  searchCourses,
} from "../../../store/actions/adminActions.ts";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";
import { INITIAL_COURSE } from "../../../common/helpers/commonConstants.ts";
import { ParamsType } from "../../../api/adminApi/types.ts";

const AdminCoursesTab = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const courses = useSelector((state: AppRootStateType) => state.admin.courses);
  const dispatch = useDispatch<AppDispatchType>();

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchCourses(params));
    } else {
      dispatch(getCourses(params));
    }
  };

  return (
    <>
      <AdminList<any>
        data={courses}
        itemName={"name"}
        itemLink={(course) => `${Path.courseDetail}/${course.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createCourse(INITIAL_COURSE))}
      />
    </>
  );
};

export default AdminCoursesTab;
