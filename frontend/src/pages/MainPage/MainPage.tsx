import Hero from "./modules/Hero/Hero.tsx";
import Courses from "./modules/Courses/Courses.tsx";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";

const MainPage = () => {
  const dispatch = useDispatch<AppDispatchType>();

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  return (
    <>
      <Hero />
      <Courses />
    </>
  );
};

export default MainPage;
