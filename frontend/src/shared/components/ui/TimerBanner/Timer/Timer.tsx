import s from "./Timer.module.scss";
import { Clock } from "../../../../assets/icons";
import CountdownTimer from "../../CountdownTimer/CountdownTimer.tsx";

const Timer = ({ appearance }: { appearance?: "dark" | "primary" }) => {
  return (
    <div className={`${s.timer} ${appearance ? s[appearance] : ""}`}>
      <Clock />
      <CountdownTimer />
    </div>
  );
};

export default Timer;
