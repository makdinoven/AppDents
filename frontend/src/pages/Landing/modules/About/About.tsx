import s from "./About.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Book } from "../../../../assets/icons/index.ts";
import { Glasses } from "../../../../assets/icons/index.ts";
import { Percent } from "../../../../assets/icons/index.ts";
import { Dollar } from "../../../../assets/icons/index.ts";
import { Clock } from "../../../../assets/icons/index.ts";
import { Calendar } from "../../../../assets/icons/index.ts";

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
