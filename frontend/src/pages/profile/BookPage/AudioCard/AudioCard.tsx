import s from "./AudioCard.module.scss";
import { Headphones } from "../../../../shared/assets/icons";
import { t } from "i18next";
import AudioPlayer from "../../../../shared/components/AudioPlayer/AudioPlayer.tsx";

interface AudioCardProps {
  title: string;
  index: number;
  audioUrl: string;
}

const AudioCard = ({ title, index, audioUrl }: AudioCardProps) => {
  const setCardColor = () => {
    if (index % 2 !== 0) {
      return s.blue;
    }
  };
  return (
    <div className={`${s.audio_card} ${setCardColor()}`}>
      <h3 className={s.chapter_name}>
        <Headphones className={s.headphones} />
        <span>
          {t("profile.bookPage.audioCard.chapter")} {index + 1}.
        </span>
        {title}
      </h3>
      <div className={s.controls}>
        <button className={s.download_audio}>
          {t("profile.bookPage.audioCard.downloadButton")}
        </button>
        <AudioPlayer
          audioUrl={
            audioUrl ||
            "https://www.learningcontainer.com/wp-content/uploads/2020/02/Kalimba.mp3"
          }
          type="default"
          index={index}
        />
      </div>
    </div>
  );
};

export default AudioCard;
