import s from "./ReferralSection.module.scss";
import { Trans } from "react-i18next";
import PrettyButton from "@/shared/components/ui/PrettyButton/PrettyButton.tsx";
import { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import { AppRootStateType } from "@/shared/store/store.ts";
import { scrollToElementById } from "@/shared/common/helpers/helpers.ts";
import {
  BASE_URL,
  LS_REF_LINK_KEY,
  REF_CODE_PARAM,
} from "@/shared/common/helpers/commonConstants.ts";
import { userApi } from "@/shared/api/userApi/userApi.ts";
import { Chevron, Clipboard, UserPlusIcon } from "@/shared/assets/icons";
import ModalOverlay from "@/shared/components/Modals/ModalOverlay/ModalOverlay.tsx";
import FriendMailInput from "../FriendMailInput/FriendMailInput.tsx";
import useOutsideClick from "@/shared/common/hooks/useOutsideClick.ts";

const highlighted = { 1: <span className={s.highlighted}></span> };

const steps = [
  {
    step: (
      <Trans i18nKey={"profile.referral.step_1"} components={highlighted} />
    ),
  },
  {
    step: (
      <Trans i18nKey={"profile.referral.step_2"} components={highlighted} />
    ),
  },
  {
    step: (
      <Trans i18nKey={"profile.referral.step_3"} components={highlighted} />
    ),
  },
  {
    step: (
      <Trans i18nKey={"profile.referral.step_4"} components={highlighted} />
    ),
  },
];

const ReferralSection = () => {
  const [showInviteFriendModal, setShowInviteFriendModal] = useState(false);
  const [refLink, setRefLink] = useState(
    localStorage.getItem(LS_REF_LINK_KEY) || "",
  );
  const [isStepsOpen, setIsStepsOpen] = useState(false);
  const balance = useSelector((state: AppRootStateType) => state.user.balance);
  const [copied, setCopied] = useState<boolean>(false);
  const closeModalRef = useRef<() => void>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const handleCopy = async () => {
    if (refLink) {
      try {
        await navigator.clipboard.writeText(refLink);
        setCopied(true);
        setTimeout(() => setCopied(false), 3000);
      } catch (err) {
        console.error("Не удалось скопировать ссылку:", err);
      }
    }
  };

  useEffect(() => {
    if (refLink) return;
    getRefLink();
  }, []);

  const getRefLink = async () => {
    try {
      const res = await userApi.getRefLink();
      const refLinkRes = `${BASE_URL}/?${REF_CODE_PARAM}=${res.data.referral_link}`;
      setRefLink(refLinkRes);
      localStorage.setItem(LS_REF_LINK_KEY, refLinkRes);
    } catch (e: any) {
      console.log(e);
    }
  };

  const handleModalClose = () => {
    setShowInviteFriendModal(false);
  };

  useOutsideClick(modalRef, () => {
    handleModalClose();
    closeModalRef.current?.();
  });

  return (
    <>
      <div className={s.section}>
        <div className={s.section_header}>
          <h4>
            <Trans
              i18nKey="profile.referral.balance"
              values={{ count: balance }}
              components={{ 1: <span className={s.highlight}></span> }}
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
            <Chevron
              onClick={() => setIsStepsOpen(!isStepsOpen)}
              className={`${isStepsOpen ? s.open : ""}`}
            />
            <button
              onClick={() => setIsStepsOpen(!isStepsOpen)}
              className={s.info_circle}
            >
              i
            </button>
          </p>
          <ul className={`${s.steps} ${isStepsOpen ? s.open : ""}`}>
            {steps.map((step, i) => (
              <li key={i}>{step.step}</li>
            ))}
          </ul>
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
              {!refLink ? "..." : refLink.replace("https://", "")}
            </span>
          </div>

          <div className={s.buttons}>
            <button className={s.copy_button} onClick={handleCopy}>
              <Clipboard />
              <Trans i18nKey={!copied ? "copy" : "copied"} />
            </button>
            <button
              className={s.invite_button}
              onClick={() => setShowInviteFriendModal(true)}
            >
              <UserPlusIcon />
              <Trans i18nKey={"profile.referrals.inviteFriend"} />
            </button>
          </div>
        </div>
      </div>

      <ModalOverlay
        isVisibleCondition={showInviteFriendModal}
        modalPosition="top"
        customHandleClose={handleModalClose}
        onInitClose={(fn) => (closeModalRef.current = fn)}
      >
        <FriendMailInput
          closeModal={() => closeModalRef.current?.()}
          ref={modalRef}
        />
      </ModalOverlay>
    </>
  );
};

export default ReferralSection;
