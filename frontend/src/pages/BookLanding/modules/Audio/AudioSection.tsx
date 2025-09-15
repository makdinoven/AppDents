import React from "react";
import s from "./AudioSection.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Trans, useTranslation } from "react-i18next";
import AudioPlayer from "../../../../components/CommonComponents/AudioPlayer/AudioPlayer.tsx";
import { Headphones } from "../../../../assets/icons";

interface AudioSectionProps {
  title: string;
  audioUrl: string;
}

const AudioSection: React.FC<AudioSectionProps> = ({
  title,
  audioUrl,
}: AudioSectionProps) => {
  const { t } = useTranslation();
  return (
    <div className={s.section_wrapper}>
      <SectionHeader name={t("bookLanding.audioPreviewAvailable")} />
      <div className={s.audio_section}>
        <div className={s.title}>
          <Headphones />
          <h3>{title}</h3>
        </div>
        <div className={s.audio_player}>
          <AudioPlayer
            audioUrl={
              "https://www.learningcontainer.com/wp-content/uploads/2020/02/Kalimba.mp3"
            }
          />
          <p>
            <Trans
              i18nKey="bookLanding.audioText"
              components={[<span className={s.highlight} />]}
            />
          </p>
        </div>
      </div>
    </div>
  );
};

export default AudioSection;
