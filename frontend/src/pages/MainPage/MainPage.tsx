import Hero from "./Hero/Hero.tsx";
import CoursesSection from "./CoursesSection/CoursesSection.tsx";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
// import Feedback from "../../components/CommonComponents/Feedback/Feedback.tsx";

const MainPage = () => {
  const dispatch = useDispatch<AppDispatchType>();

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  return (
    <>
      <Hero />
      <CoursesSection />
      {/*<Feedback />*/}
    </>
  );
};

export default MainPage;
