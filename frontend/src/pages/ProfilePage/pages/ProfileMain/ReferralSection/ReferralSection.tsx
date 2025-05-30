import s from "./ReferralSection.module.scss";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../store/store.ts";
import { scrollToElementById } from "../../../../../common/helpers/helpers.ts";
import {
  BASE_URL,
  REF_CODE_PARAM,
} from "../../../../../common/helpers/commonConstants.ts";
import { userApi } from "../../../../../api/userApi/userApi.ts";

const ReferralSection = () => {
  const [refLink, setRefLink] = useState("");
  const [isStepsOpen, setIsStepsOpen] = useState(false);
  const balance = useSelector((state: AppRootStateType) => state.user.balance);
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = async () => {
    if (refLink) {
      try {
        await navigator.clipboard.writeText(refLink);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error("Не удалось скопировать ссылку:", err);
      }
    }
  };

  useEffect(() => {
    getRefLink();
  }, []);

  const getRefLink = async () => {
    try {
      const res = await userApi.getRefLink();
      setRefLink(`${BASE_URL}/?${REF_CODE_PARAM}=${res.data.referral_link}`);
    } catch (e: any) {
      console.log(e);
    }
  };

  const steps = [
    {
      step: (
        <Trans
          i18nKey={"profile.referral.step_1"}
          components={{ 1: <span className={s.highlighted}></span> }}
        />
      ),
    },
    {
      step: (
        <Trans
          i18nKey={"profile.referral.step_2"}
          components={{ 1: <span className={s.highlighted}></span> }}
        />
      ),
    },
    {
      step: (
        <Trans
          i18nKey={"profile.referral.step_3"}
          components={{ 1: <span className={s.highlighted}></span> }}
        />
      ),
    },
    {
      step: (
        <Trans
          i18nKey={"profile.referral.step_4"}
          components={{ 1: <span className={s.highlighted}></span> }}
        />
      ),
    },
  ];

  return (
    <div className={s.section}>
      <div className={s.section_header}>
        <h4>
          <Trans
            i18nKey="profile.referral.balance"
            values={{ count: balance }}
            components={{ 1: <span className="highlight"></span> }}
          />
        </h4>
        <PrettyButton
          onClick={() => scrollToElementById("profile_courses")}
          className={s.spend}
          variant={"primary"}
          text={"profile.referral.spend"}
        />
      </div>

      <div className={s.section_middle}>
        <p className={s.invite_row}>
          <Trans i18nKey="profile.referral.invite" />
          <button
            onClick={() => setIsStepsOpen(!isStepsOpen)}
            className={s.info_circle}
          >
            i
          </button>
        </p>
        {/*{isStepsOpen && (*/}
        <ul className={`${s.steps} ${isStepsOpen ? s.open : ""}`}>
          {steps.map((step, i) => (
            <li key={i}>{step.step}</li>
          ))}
        </ul>
        {/*)}*/}
        <p className={s.friends}>
          <Trans
            i18nKey={"profile.referral.friendsPurchases"}
            components={{ 1: <span className={s.highlighted}></span> }}
          />
        </p>
      </div>

      <div className={s.section_bottom}>
        <div className={s.invite_link_wrapper}>
          <Trans i18nKey="profile.referral.link" />{" "}
          <span className={s.invite_link} onClick={handleCopy}>
            {refLink.replace("https://", "")}
          </span>
        </div>

        <PrettyButton
          onClick={handleCopy}
          variant={"default_white_hover"}
          className={s.copy_button}
          text={!copied ? "copy" : "copied"}
        />
      </div>
    </div>
  );
};

export default ReferralSection;
