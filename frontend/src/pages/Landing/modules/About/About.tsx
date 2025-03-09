import s from "./About.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import Book from "../../../../common/Icons/Book.tsx";
import Glasses from "../../../../common/Icons/Glasses.tsx";
import Percent from "../../../../common/Icons/Percent.tsx";
import Dollar from "../../../../common/Icons/Dollar.tsx";
import Clock from "../../../../common/Icons/Clock.tsx";
import Calendar from "../../../../common/Icons/Calendar.tsx";

const About = ({ data }: { data: any }) => {
  const aboutItems = [
    { Icon: Book, text: data.lessonsCount },
    { Icon: Percent, text: data.discount },
    { Icon: Calendar, text: data.access },
    { Icon: Glasses, text: data.professorsCount },
    { Icon: Dollar, text: data.savings },
    { Icon: Clock, text: data.duration },
  ];

  return (
    <section className={s.about}>
      <SectionHeader name={"landing.about"} />
      <ul>
        {aboutItems.map((item, index) => (
          <li key={index} className={s.about_item}>
            <item.Icon />
            {item.text}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default About;
