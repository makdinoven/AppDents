import s from "./About.module.scss";
import SectionHeader from "../../../../shared/components/ui/SectionHeader/SectionHeader.tsx";
import {
  BookAbout,
  CalendarAbout,
  Clock,
  DollarAbout,
  Glasses,
  LightningAbout,
  Percent,
} from "../../../../shared/assets/icons/index.ts";

const About = ({
  data: {
    lessonsCount,
    discount,
    access,
    professorsCount,
    savings,
    duration,
    instantAccess,
  },
  type,
}: {
  data: any;
  type?: "book" | "landing";
}) => {
  const aboutItems = [
    professorsCount && { Icon: Glasses, text: professorsCount },
    lessonsCount && { Icon: BookAbout, text: lessonsCount },
    duration && { Icon: Clock, text: duration },
    access && { Icon: CalendarAbout, text: access },
    discount && { Icon: Percent, text: discount },
    savings && { Icon: DollarAbout, text: savings },
    instantAccess && { Icon: LightningAbout, text: instantAccess },
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
