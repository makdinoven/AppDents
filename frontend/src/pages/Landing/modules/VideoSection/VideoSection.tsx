import s from "./VideoSection.module.scss";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Glasses } from "../../../../assets/icons";
import { Book } from "../../../../assets/icons";
import Clock from "../../../../assets/icons/Clock.tsx";
import { Calendar } from "../../../../assets/icons";
import { Percent } from "../../../../assets/icons";
import Dollar from "../../../../assets/icons/Dollar.tsx";
import { Trans } from "react-i18next";
import { PlayIcon } from "../../../../assets/icons";
import AuthorsDesc from "../../../../components/ui/AuthorsDesc/AuthorsDesc.tsx";
import Button from "../../../../components/ui/Button/Button.tsx";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../../../store/store.ts";
import { openModal } from "../../../../store/slices/landingSlice.ts";
import ExpandableText from "../../../../components/ui/ExpandableText/ExpandableText.tsx";
import { useScreenWidth } from "../../../../common/hooks/useScreenWidth.ts";
import SuggestionLessons from "./modules/SuggestionLessons/SuggestionLessons.tsx";
import SuggestionLessonsSlider from "./modules/SuggestionLessonsSlider/SuggestionLessonsSlider.tsx";

const VideoSection = ({
  data: { lessons, about, course_program, authors, landing_name },
}: {
  data: any;
}) => {
  const dispatch = useDispatch<AppDispatchType>();
  const [currentLesson, setCurrentLesson] = useState(lessons[0]);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const lessonContainerRef = useRef<HTMLDivElement | null>(null);
  const lessonDescRef = useRef<HTMLDivElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [lessonHeight, setLessonHeight] = useState<number | undefined>(
    undefined
  );
  const [isPlayerModalVisible, setIsPlayerModalVisible] = useState<boolean>();
  const screenWidth = useScreenWidth();

  useLayoutEffect(() => {
    if (lessonContainerRef.current) {
      setLessonHeight(lessonContainerRef.current.offsetHeight);
    }
    setIsPlayerModalVisible(false);
    setIsPlaying(false);
  }, [currentLesson]);

  useEffect(() => {
    if (!lessonContainerRef.current || screenWidth < 769) return;

    const observer = new ResizeObserver(() => {
      setLessonHeight(lessonContainerRef.current!.offsetHeight);
    });

    observer.observe(lessonContainerRef.current);

    return () => observer.disconnect();
  }, []);

  const togglePlay = () => {
    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }

    setIsPlaying(!isPlaying);
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      if (video.currentTime >= 120 && !isPlayerModalVisible) {
        videoRef.current!.pause();
        setIsPlayerModalVisible(true);
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [isPlayerModalVisible, dispatch]);

  const aboutItems = [
    { Icon: Glasses, text: about.professorsCount },
    { Icon: Book, text: about.lessonsCount },
    { Icon: Clock, text: about.duration },
    { Icon: Calendar, text: about.access },
    { Icon: Percent, text: about.discount },
    { Icon: Dollar, text: about.savings },
  ];

  return (
    <section className={s.video_section}>
      <div className={s.player_container}>
        <div ref={lessonContainerRef} className={s.current_lesson_container}>
          <div className={s.player}>
            <video
              playsInline
              webkit-playsinline
              disablePictureInPicture
              onClick={togglePlay}
              ref={videoRef}
              poster={currentLesson.preview}
              src={currentLesson.link}
            ></video>
            {!isPlaying && (
              <button onClick={togglePlay} className={s.play_button}>
                <PlayIcon />
              </button>
            )}
            {isPlayerModalVisible && (
              <div className={s.video_modal}>
                <div className={s.video_modal_content}>
                  <h5>
                    <Trans i18nKey={"landing.video.modalTitle"} />
                  </h5>
                  <p>
                    <Trans i18nKey={"landing.video.buyCourseToWatch"} />
                  </p>
                  <Button
                    onClick={() => dispatch(openModal())}
                    text={"buy"}
                    variant={"outlined"}
                  />
                </div>
              </div>
            )}
            <div className={s.lesson_duration}>{currentLesson.duration}</div>
          </div>
          <div className={s.lesson_description}>
            <h4>{currentLesson.name}</h4>
            {currentLesson.program && (
              <ExpandableText
                ref={lessonDescRef}
                lines={screenWidth > 577 ? 4 : 2}
                textClassName={s.lesson_desc_text}
                text={currentLesson.program}
                color={"primary"}
              />
            )}
            <div className={s.authors_btn_container}>
              <AuthorsDesc authors={authors} size={"large"} />
              <Button
                onClick={() => dispatch(openModal())}
                text={"buy"}
                variant={"outlined-dark"}
              />
            </div>
          </div>
        </div>

        {lessons.length > 0 && screenWidth >= 769 && (
          <SuggestionLessons
            maxHeight={lessonHeight}
            setCurrentLesson={setCurrentLesson}
            currentLesson={currentLesson}
            lessons={lessons}
          />
        )}
      </div>

      <h1 className={s.landing_name}>{landing_name}</h1>

      <ul className={s.about_list}>
        {aboutItems.length > 0 &&
          aboutItems.map((item: any, index: number) => (
            <li key={index} className={s.about_item}>
              <item.Icon />
              {item.text}
            </li>
          ))}
      </ul>

      <div className={s.about_container}>
        <h5>
          <Trans i18nKey={"landing.about"} />
        </h5>
        <ExpandableText
          lines={screenWidth > 577 ? 6 : 3}
          textClassName={s.course_program_text}
          text={course_program}
          color={"light"}
        />
      </div>

      {screenWidth < 769 && (
        <SuggestionLessonsSlider
          setCurrentLesson={setCurrentLesson}
          currentLesson={currentLesson}
          lessons={lessons}
        />
      )}
      {/*<span className={s.line}></span>*/}
    </section>
  );
};

export default VideoSection;
