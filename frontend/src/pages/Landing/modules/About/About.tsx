import s from "./About.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import Book from "../../../../common/Icons/Book.tsx";
import Glasses from "../../../../common/Icons/Glasses.tsx";
import Percent from "../../../../common/Icons/Percent.tsx";
import Dollar from "../../../../common/Icons/Dollar.tsx";
import Clock from "../../../../common/Icons/Clock.tsx";

const About = ({ data }: { data: any }) => {
  return (
    <section className={s.about}>
      <SectionHeader name={"landing.about"} />
      <ul>
        <li className={s.about_item}>
          <Book />
          {data.lessonsCount}
        </li>
        <li className={s.about_item}>
          <Glasses />
          {data.professorsCount}
        </li>
        <li className={s.about_item}>
          <Percent />
          {data.discount}
        </li>
        <li className={s.about_item}>
          <Dollar />
          {data.savings}
        </li>
        <li className={s.about_item}>
          <Clock />
          {data.access}
        </li>
      </ul>
    </section>
  );
};

export default About;
