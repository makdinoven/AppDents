import { useRef, useState, useEffect } from "react";
import s from "./AudioPlayer.module.scss";
import { Control, PauseCircle, PlayCircle } from "../../../assets/icons";

interface AudioPlayerProps {
  audioUrl: string;
  type?: "default" | "landing";
  index?: number;
}

const AudioPlayer = ({
  audioUrl,
  type = "landing",
  index,
}: AudioPlayerProps) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(180);
  const [currentTime, setCurrentTime] = useState(0);

  const isDefault = type === "default";
  const isBlue = index !== undefined && index % 2 !== 0;

  const colorClass = isDefault ? (isBlue ? s.blue : s.primary) : "";

  const getColorValue = (opacity = 1) => {
    if (type === "landing") return `rgb(237, 248, 255, ${opacity})`;
    return isBlue
      ? `rgba(121, 206, 231, ${opacity})`
      : `rgba(127, 223, 213, ${opacity})`;
  };

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

    let animationFrameId: number;

    const updateProgress = () => {
      setCurrentTime(audio.currentTime);
      setProgress((audio.currentTime / audio.duration) * 100);
      animationFrameId = requestAnimationFrame(updateProgress);
    };

    const handlePlay = () => {
      animationFrameId = requestAnimationFrame(updateProgress);
    };

    const handlePause = () => {
      cancelAnimationFrame(animationFrameId);
    };

    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("loadedmetadata", () => setDuration(audio.duration));

    return () => {
      cancelAnimationFrame(animationFrameId);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
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

      <div className={`${s.custom_player} ${s[type]}`}>
        {type === "landing" && <p className={s.mp3}>mp3</p>}

        <div className={`${s.controls} ${s.default}`}>
          <button disabled className={`${s.previous} ${colorClass}`}>
            <Control />
          </button>

          <button
            onClick={togglePlay}
            className={`${s.play_button} ${!audioUrl && s.disabled} ${colorClass}`}
            disabled={!audioUrl}
          >
            {isPlaying ? (
              <PauseCircle className={s.pause} />
            ) : (
              <PlayCircle className={s.play} />
            )}
          </button>

          <button disabled className={`${s.next} ${colorClass}`}>
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
            className={`${s.progress} ${colorClass}`}
            style={{
              background: `linear-gradient(to right, ${getColorValue()} ${progress}%, ${getColorValue(0.6)} ${progress}%)`,
            }}
          />

          <div className={s.time_info}>
            <span className={`${s.time} ${colorClass}`}>
              {formatTime(currentTime)}
            </span>
            <span className={`${s.time} ${colorClass}`}>
              {formatTime(currentTime, duration)}
            </span>
          </div>
        </div>
      </div>
    </>
  );
};

export default AudioPlayer;
