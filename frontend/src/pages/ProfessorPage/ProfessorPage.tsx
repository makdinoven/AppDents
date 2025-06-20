import s from "./ProfessorPage.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import { useParams } from "react-router-dom";
import { useSelector } from "react-redux";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";
import CardsList from "../../components/CommonComponents/CoursesSection/CardsList/CardsList.tsx";
import SectionHeader from "../../components/ui/SectionHeader/SectionHeader.tsx";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../components/ui/ArrowButton/ArrowButton.tsx";
import Clock from "../../assets/Icons/Clock.tsx";
import ModalWrapper from "../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PaymentModal from "../../components/Modals/PaymentModal/PaymentModal.tsx";
import { BASE_URL } from "../../common/helpers/commonConstants.ts";
import { Path } from "../../routes/routes.ts";
import { useScreenWidth } from "../../common/hooks/useScreenWidth.ts";
import ExpandableText from "../../components/ui/ExpandableText/ExpandableText.tsx";

const ProfessorPage = () => {
  const { professorId } = useParams();
  const [professor, setProfessor] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const language = useSelector((state: any) => state.user.language);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const currentUrl = window.location.origin + location.pathname;
  const screenWidth = useScreenWidth();

  useEffect(() => {
    fetchProfessorData();
  }, [professorId]);

  const fetchProfessorData = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getProfessorDetail(Number(professorId));
      setProfessor(res.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const paymentData = {
    landing_ids: professor?.landings.map(
      (landing: { id: number }) => landing.id,
    ),
    course_ids: professor?.course_ids,
    price_cents: professor?.total_new_price * 100,
    total_new_price: professor?.total_new_price,
    total_old_price: professor?.total_old_price,
    region: language,
    success_url: `${BASE_URL}${Path.successPayment}`,
    cancel_url: currentUrl,
    courses: professor?.landings.map(
      (item: {
        landing_name: string;
        new_price: number;
        old_price: number;
      }) => ({
        name: item.landing_name,
        new_price: item.new_price,
        old_price: item.old_price,
      }),
    ),
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const renderBuySection = () => {
    return (
      <section className={s.buy_section}>
        <div className={s.professor_access}>
          <Clock />
          <p>
            <Trans i18nKey="professor.accessToAllCourses" />
          </p>
        </div>
        <p className={s.buy_section_desc}>
          <Trans
            i18nKey="professor.youCanBuyAllCourses"
            values={{
              new_price: professor.total_new_price,
              old_price: professor.total_old_price,
            }}
            components={{
              1: <span className="highlight" />,
              2: <span className="crossed" />,
            }}
          />
        </p>
        <ArrowButton onClick={() => setIsModalOpen(true)}>
          <Trans
            i18nKey={"professor.getAllCourses"}
            values={{
              new_price: professor.total_new_price,
            }}
            components={{
              1: <span className="highlight" />,
            }}
          />
        </ArrowButton>
      </section>
    );
  };

  return (
    <>
      <BackButton />
      {loading || !professor ? (
        <Loader />
      ) : (
        <div className={s.professor_page}>
          <section className={s.professor_hero}>
            {screenWidth < 577 && (
              <h1 className={s.professor_name}>{professor.name}</h1>
            )}
            <div className={s.professor_info}>
              {screenWidth > 577 && (
                <h1 className={s.professor_name}>{professor.name}</h1>
              )}
              <ExpandableText
                lines={screenWidth > 577 ? 10 : 3}
                textClassName={s.professor_description}
                text={professor.description}
                color={"primary"}
              />
              {/*<p className={s.professor_description}>{professor.description}</p>*/}
            </div>
            {professor.photo && (
              <div className={s.card_wrapper}>
                <div className={s.card}>
                  <div className={s.card_header}></div>
                  <div className={s.card_body}>
                    <div className={s.photo}>
                      <img src={professor.photo} alt="Professor image" />
                    </div>
                  </div>
                  <div className={s.card_bottom}></div>
                </div>
              </div>
            )}
          </section>
          {renderBuySection()}
          <div className={s.professor_cards}>
            <SectionHeader name={"professor.professorsCourses"} />
            <CardsList
              // isClient={true}
              filter={"all"}
              loading={false}
              cards={professor.landings}
              showSeeMore={false}
              showEndOfList={false}
            />
          </div>
          {renderBuySection()}
          <CoursesSection
            isOffer={true}
            showSort={true}
            sectionTitle={"other.otherCourses"}
            pageSize={6}
          />
        </div>
      )}
      {isModalOpen && (
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

export default ProfessorPage;
