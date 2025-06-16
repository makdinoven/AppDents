import { useEffect, useState } from "react";
import { t } from "i18next";

const CountdownTimer = ({ endsAt }: { endsAt?: string }) => {
  const [timeLeft, setTimeLeft] = useState("");

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();

      const targetTime = endsAt
        ? new Date(endsAt)
        : (() => {
            const midnight = new Date();
            midnight.setHours(24, 0, 0, 0);
            return midnight;
          })();

      const diff = targetTime.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeLeft("00:00:00");
        return;
      }

      const totalSeconds = Math.floor(diff / 1000);
      const days = Math.floor(totalSeconds / (60 * 60 * 24));
      const hours = Math.floor((totalSeconds % (60 * 60 * 24)) / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;

      const timeString =
        (days > 0 ? `${days}${t("daysShort")} ` : "") +
        `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

      setTimeLeft(timeString);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [endsAt]);

  return <>{timeLeft}</>;
};

export default CountdownTimer;
