import { useDispatch, useSelector } from "react-redux";
import {
  createCourse,
  getCourses,
} from "../../../store/actions/adminActions.ts";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";

const initialCourse = {
  name: "New course",
  description: "",
};

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
        onCreate={() => dispatch(createCourse(initialCourse))}
        searchPlaceholder="admin.courses.search"
        createButtonText="admin.courses.create"
        notFoundText="admin.courses.notFound"
      />
    </>
  );
};

export default Courses;
