import s from "./About.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Book, LightningAbout } from "../../../../assets/icons/index.ts";
import { Glasses } from "../../../../assets/icons/index.ts";
import { Percent } from "../../../../assets/icons/index.ts";
import { Dollar } from "../../../../assets/icons/index.ts";
import { Clock } from "../../../../assets/icons/index.ts";
import { Calendar } from "../../../../assets/icons/index.ts";

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
    lessonsCount && { Icon: Book, text: lessonsCount },
    duration && { Icon: Clock, text: duration },
    access && { Icon: Calendar, text: access },
    discount && { Icon: Percent, text: discount },
    savings && { Icon: Dollar, text: savings },
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
