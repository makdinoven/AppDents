import { useDispatch, useSelector } from "react-redux";
import {
  createCourse,
  getCourses,
} from "../../../../store/actions/adminActions.ts";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
import AdminList from "./AdminList.tsx";
import { Path } from "../../../../routes/routes.ts";
import { CourseType } from "../../types.ts";

const initialCourse: CourseType = {
  name: "New Course",
  description: "",
  landing: {
    title: "",
    old_price: 0,
    price: 0,
    main_image: "",
    main_text: "",
    language: "en",
    tag_id: 1,
    authors: [],
    sales_count: 0,
  },
  sections: [],
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
