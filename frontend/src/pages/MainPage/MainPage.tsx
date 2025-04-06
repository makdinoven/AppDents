import Hero from "./modules/Hero/Hero.tsx";
import CoursesSection from "./modules/CoursesSection/CoursesSection.tsx";
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
      <CoursesSection />
    </>
  );
};

export default MainPage;
