import s from "../Landing/Landing.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import Faq from "../Landing/modules/Faq/Faq.tsx";
import BookLandingHero from "./modules/BookLandingHero/BookLandingHero.tsx";
import { useEffect, useState } from "react";
import ContentOverview from "./modules/ContentOverview/ContentOverview.tsx";
import AudioSection from "./modules/Audio/AudioSection.tsx";
import BuySection from "../../components/CommonComponents/BuySection/BuySection.tsx";
import { FORMATS } from "../../common/helpers/commonConstants.ts";
import Professors from "./modules/Professors/Professors.tsx";

const BookLanding = () => {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    fetch(
      "http://test.dent-s.com/api/books/landing/slug/zero-bone-loss-concepts-book",
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error("Fetch error: " + response.statusText);
        }
        return response.json();
      })
      .then((data) => {
        console.log(data);
        setData(data);
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
      });
  }, []);

  return (
    <>
      <div className={s.landing_top}>
        <BackButton />
      </div>

      <div className={s.landing}>
        {data ? (
          <>
            {/* <BookLandingHero data={data} loading={false} /> */}
            <ContentOverview books={data.books} />
            <BuySection
              type="download"
              isFullWidth={true}
              oldPrice={data.old_price}
              newPrice={data.new_price}
              formats={FORMATS}
            />
            <AudioSection audioUrl="" title="NYSORA Nerve Block Manual" />
            <Professors professors={data.authors} />
            <Faq type={"book"} />
          </>
        ) : (
          <></>
        )}
      </div>
    </>
  );
};

export default BookLanding;
