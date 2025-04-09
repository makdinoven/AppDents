import { useDispatch, useSelector } from "react-redux";
import {
  createCourse,
  getCourses,
} from "../../../store/actions/adminActions.ts";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";
import { INITIAL_COURSE } from "../../../common/helpers/commonConstants.ts";

const Courses = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const courses = useSelector((state: AppRootStateType) => state.admin.courses);
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        items={courses}
        searchField="name"
        itemName="name"
        itemLink={(course) => `${Path.courseDetail}/${course.id}`}
        loading={loading}
        onFetch={() => dispatch(getCourses())}
        onCreate={() => dispatch(createCourse(INITIAL_COURSE))}
        searchPlaceholder="admin.courses.search"
        createButtonText="admin.courses.create"
        notFoundText="admin.courses.notFound"
      />
    </>
  );
};

export default Courses;
