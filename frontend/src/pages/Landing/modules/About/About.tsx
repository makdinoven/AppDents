import s from "./About.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import Book from "../../../../assets/icons/Book.tsx";
import Glasses from "../../../../assets/icons/Glasses.tsx";
import Percent from "../../../../assets/icons/Percent.tsx";
import Dollar from "../../../../assets/icons/Dollar.tsx";
import Clock from "../../../../assets/icons/Clock.tsx";
import Calendar from "../../../../assets/icons/Calendar.tsx";

const About = ({
  data: { lessonsCount, discount, access, professorsCount, savings, duration },
}: {
  data: any;
}) => {
  const aboutItems = [
    { Icon: Glasses, text: professorsCount },
    { Icon: Book, text: lessonsCount },
    { Icon: Clock, text: duration },
    { Icon: Calendar, text: access },
    { Icon: Percent, text: discount },
    { Icon: Dollar, text: savings },
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
