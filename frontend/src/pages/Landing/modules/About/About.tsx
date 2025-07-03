import s from "./About.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import Book from "../../../../assets/Icons/Book.tsx";
import Glasses from "../../../../assets/Icons/Glasses.tsx";
import Percent from "../../../../assets/Icons/Percent.tsx";
import Dollar from "../../../../assets/Icons/Dollar.tsx";
import Clock from "../../../../assets/Icons/Clock.tsx";
import Calendar from "../../../../assets/Icons/Calendar.tsx";

const About = ({
  data: { lessonsCount, discount, access, professorsCount, savings, duration },
  type,
}: {
  data: any;
  type?: "book" | "landing";
}) => {
  const aboutItems = [
    professorsCount && { Icon: Glasses, text: professorsCount },
    lessonsCount && { Icon: Book, text: lessonsCount },
    duration && { Icon: Clock, text: duration },
    access && { Icon: Calendar, text: access },
    discount && { Icon: Percent, text: discount },
    savings && { Icon: Dollar, text: savings },
  ].filter(Boolean);

  return (
    <section className={s.about}>
      <SectionHeader name={type ? "bookLanding.about" : "landing.about"} />
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
