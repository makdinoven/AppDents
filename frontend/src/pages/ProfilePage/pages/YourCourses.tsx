import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../shared/store/store.ts";
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { getCourses } from "../../../shared/store/actions/userActions.ts";
import MyContent from "./modules/MyContent/MyContent.tsx";

const YourCourses = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const location = useLocation();
  const childKey = location.pathname.slice(1);

  useEffect(() => {
    if (!courses.length) dispatch(getCourses());
  }, []);

  return (
    <MyContent key={childKey} showSearch={true} items={courses} type="course" />
  );
};

export default YourCourses;
