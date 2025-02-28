import s from "./Courses.module.scss";
import { Trans } from "react-i18next";

const Courses = () => {
  return (
    <section className={s.courses}>
      <div className={s.courses_header}>
        <h3>
          <Trans i18nKey={"main.ourCurses"} />
        </h3>
      </div>
    </section>
  );
};
export default Courses;
