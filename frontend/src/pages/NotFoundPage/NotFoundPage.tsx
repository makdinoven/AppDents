import s from "./NotFoundPage.module.scss";
import { useNavigate } from "react-router-dom";
import PrettyButton from "../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import { Trans } from "react-i18next";
import { PATHS } from "../../app/routes/routes.ts";

const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className={s.page_container}>
      <div>
        <span>
          <Trans i18nKey={"pageNotFound.num"} />
        </span>
        <p className={s.page_not_found}>
          <Trans i18nKey={"pageNotFound.title"} />
        </p>
        <p>
          <Trans i18nKey={"pageNotFound.sorry"} />
        </p>
      </div>

      <PrettyButton
        variant={"primary"}
        text={"pageNotFound.backToHome"}
        onClick={() => navigate(PATHS.MAIN)}
      />
    </div>
  );
};

export default NotFoundPage;
