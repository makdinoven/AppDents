import s from "./ProductDetails.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Book, GlobeIcon } from "../../../../assets/icons/index.ts";
import { Glasses } from "../../../../assets/icons/index.ts";
import { Percent } from "../../../../assets/icons/index.ts";
import { Dollar } from "../../../../assets/icons/index.ts";
import { Clock } from "../../../../assets/icons/index.ts";
import { Calendar } from "../../../../assets/icons/index.ts";

const ProductDetails = ({
  data: {
    pages_count: pagesCount,
    discount,
    access,
    publisher,
    savings,
    publicationDate: publicationDate,
    language,
  },
}: {
  data: any;
}) => {
  const aboutItems = [
    publisher && { Icon: Glasses, text: publisher },
    pagesCount && { Icon: Book, text: pagesCount },
    publicationDate && {
      Icon: Clock,
      text: publicationDate,
    },
    access && { Icon: Calendar, text: access },
    discount && { Icon: Percent, text: discount },
    savings && { Icon: Dollar, text: savings },
    language && { Icon: GlobeIcon, text: language },
  ].filter(Boolean);

  return (
    <section className={s.product_details}>
      <SectionHeader name="bookLanding.productDetails" />
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

export default ProductDetails;
