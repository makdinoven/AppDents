import s from "./AudioPlayer.module.scss";
import { useRef, useState, useEffect } from "react";
import { Control, PauseCircle, PlayCircle } from "../../../assets/icons";

interface AudioPlayerProps {
  audioUrl: string;
}

const AudioPlayer = ({ audioUrl }: AudioPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(180);
  const [currentTime, setCurrentTime] = useState(0);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateProgress = () => {
      setCurrentTime(audio.currentTime);
      setProgress((audio.currentTime / audio.duration) * 100);
    };

    const setAudioData = () => {
      setDuration(audio.duration);
    };

    audio.addEventListener("timeupdate", updateProgress);
    audio.addEventListener("loadedmetadata", setAudioData);

    return () => {
      audio.removeEventListener("timeupdate", updateProgress);
      audio.removeEventListener("loadedmetadata", setAudioData);
    };
  }, []);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;
    const newProgress = Number(e.target.value);
    audioRef.current.currentTime = (newProgress / 100) * duration;
    setProgress(newProgress);
  };

  const formatTime = (currentTime: number, duration?: number) => {
    let time = currentTime;
    let sign = "";
    if (duration) {
      time = currentTime - duration;
      sign = time <= 0 ? "-" : sign;
    }

    const newTime = Math.abs(time);
    const minutes = Math.floor(newTime / 60);
    const seconds = Math.floor(newTime % 60)
      .toString()
      .padStart(2, "0");
    return `${sign}${minutes}:${seconds}`;
  };

  return (
    <>
      <audio ref={audioRef} src={audioUrl} className={s.hidden} />

      <div className={s.custom_player}>
        <p className={s.mp3}>mp3</p>
        <div className={s.controls}>
          <button disabled className={s.previous}>
            <Control />
          </button>
          <button
            onClick={togglePlay}
            className={`${s.play_button} ${!audioUrl && s.disabled}`}
            disabled={!audioUrl}
          >
            {isPlaying ? <PauseCircle /> : <PlayCircle />}
          </button>
          <button disabled className={s.next}>
            <Control />
          </button>
        </div>
        <div className={s.progress_wrapper}>
          <input
            type="range"
            min="0"
            max="100"
            value={progress}
            onChange={handleSeek}
            className={s.progress}
            style={{
              background: `linear-gradient(to right, rgb(237, 248, 255) ${progress}%, rgba(237, 248, 255, 0.6) ${progress}%)`,
            }}
          />
          <div className={s.time_info}>
            <span className={s.time}>{formatTime(currentTime)}</span>
            <span className={s.time}>{formatTime(currentTime, duration)}</span>
          </div>
        </div>
      </div>
    </>
  );
};

export default AudioPlayer;
