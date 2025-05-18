import s from "./CourseCard.module.scss";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import { Trans } from "react-i18next";
import { Path } from "../../../../routes/routes.ts";
import { Link } from "react-router-dom";
import initialPhoto from "../../../../assets/no-pictures.png";
import FormattedAuthorsDesc from "../../../../common/helpers/FormattedAuthorsDesc.tsx";
import ViewLink from "../../../ui/ViewLink/ViewLink.tsx";
import { useState } from "react";
import ModalWrapper from "../../../Modals/ModalWrapper/ModalWrapper.tsx";
import PaymentModal, {
  PaymentDataType,
} from "../../../Modals/PaymentModal/PaymentModal.tsx";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";
import { BASE_URL } from "../../../../common/helpers/commonConstants.ts";
import LoaderOverlay from "../../../ui/LoaderOverlay/LoaderOverlay.tsx";

// import Book from "../../../../assets/Icons/Book.tsx";

interface CourseCardProps {
  name: string;
  tag: string;
  link: string;
  photo: string;
  index: number;
  old_price: number;
  new_price: number;
  authors: any[];
  lessons_count: string;
}

const CourseCard = ({
  name,
  tag,
  link,
  photo,
  old_price,
  new_price,
  index,
  authors,
  lessons_count,
}: CourseCardProps) => {
  const [paymentData, setPaymentData] = useState<PaymentDataType | null>(null);
  const [paymentDataLoading, setPaymentDataLoading] = useState(false);
  const currentUrl = window.location.origin + location.pathname;
  const [isModalOpen, setModalOpen] = useState(false);
  const screenWidth = useScreenWidth();
  const LANDING_LINK = `${Path.landing}/${link}`;
  const visibleAuthors = authors?.slice(0, 3).filter((author) => author.photo);

  const setCardColor = () => {
    if (screenWidth < 577) {
      return index % 2 === 0 ? s.blue : "";
    } else {
      return index % 4 === 0 || index % 4 === 3 ? "" : s.blue;
    }
  };

  const handleBuyClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    setPaymentDataLoading(true);
    e.preventDefault();
    e.stopPropagation();
    fetchLandingDataAndOpenModal();
  };

  const fetchLandingDataAndOpenModal = async () => {
    try {
      const res = await mainApi.getLanding(link);
      setPaymentData({
        course_ids: res.data?.course_ids,
        price_cents: res.data?.new_price * 100,
        total_new_price: res.data?.new_price,
        total_old_price: res.data?.old_price,
        region: res.data?.language,
        success_url: `${BASE_URL}${Path.successPayment}`,
        cancel_url: currentUrl,
        courses: [
          {
            name: res.data?.landing_name,
            new_price: res.data?.new_price,
            old_price: res.data?.old_price,
          },
        ],
      });
      setModalOpen(true);
      setPaymentDataLoading(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  return (
    <>
      <li className={`${s.card} ${setCardColor()}`}>
        <div className={s.card_header}>
          <Link to={LANDING_LINK} className={s.card_header_background}>
            <Trans i18nKey={tag} />
          </Link>
        </div>
        <Link to={LANDING_LINK} className={s.card_body}>
          <div className={s.card_content_header}>
            <div className={s.prices}>
              <span className={s.new_price}>${new_price}</span>{" "}
              <span className="crossed">${old_price}</span>
            </div>
            <p className={s.lessons_count}>{lessons_count}</p>
          </div>
          <div className={s.card_content_body}>
            <h4>{name}</h4>
            <div className={s.course_authors}>
              {visibleAuthors?.length > 0 && (
                <ul className={s.authors_photos_list}>
                  {visibleAuthors?.map((author) => (
                    <li
                      key={author.id}
                      style={{ backgroundImage: `url("${author.photo}")` }}
                      className={s.author_photo}
                    ></li>
                  ))}
                </ul>
              )}
              <p>
                <FormattedAuthorsDesc authors={authors} />
              </p>
            </div>
            <div className={s.content_bottom}>
              <ViewLink className={s.link_btn} text={"viewCourse"} />
              {photo ? (
                <div className={s.photo}>
                  <img src={photo} alt="Course image" />
                </div>
              ) : (
                <div className={s.photo}>
                  <div
                    style={{ backgroundImage: `url(${initialPhoto})` }}
                    className={s.no_photo}
                  ></div>
                </div>
              )}
            </div>
            <div className={s.buttons}>
              <button onClick={(e) => handleBuyClick(e)} className={s.buy_btn}>
                {paymentDataLoading && <LoaderOverlay />}
                <Trans i18nKey={"buyNow"} />
              </button>
              {/*<AddToCartButton*/}
              {/*  handleClick={() => {*/}
              {/*    console.log("cart");*/}
              {/*  }}*/}
              {/*/>*/}
            </div>
          </div>

          <Link to={LANDING_LINK} className={s.card_bottom}></Link>
        </Link>
      </li>

      {isModalOpen && paymentData && (
        <ModalWrapper
          variant="dark"
          title={"yourOrder"}
          cutoutPosition="none"
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          <PaymentModal
            paymentData={paymentData}
            handleCloseModal={handleCloseModal}
          />
        </ModalWrapper>
      )}
    </>
  );
};

export default CourseCard;
