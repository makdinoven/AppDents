import { useEffect, useRef, useState } from "react";
import s from "./ExpandableText.module.scss";
import { t } from "i18next";

type Props = {
  ref?: any;
  text: string;
  textClassName?: string;
  lines?: number;
  color: "primary" | "light" | "dark";
  showButton?: boolean;
};

const ExpandableText = ({
  text,
  lines = 3,
  color,
  textClassName,
  showButton = true,
  ref,
}: Props) => {
  const [expanded, setExpanded] = useState(false);
  const [maxHeight, setMaxHeight] = useState<number>(0);
  const [isTruncated, setIsTruncated] = useState(false);

  const contentRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (contentRef.current && textRef.current) {
      const lineHeight = parseFloat(
        getComputedStyle(contentRef.current).lineHeight || "20",
      );
      const collapsedHeight = lineHeight * lines;
      const fullHeight = textRef.current.scrollHeight;

      setMaxHeight(expanded ? fullHeight : collapsedHeight);
      setIsTruncated(fullHeight > collapsedHeight);
    }
  }, [expanded, lines, text]);

  const toggleExpanded = () => {
    setExpanded((prev) => !prev);
  };

  return (
    <div ref={ref} className={s.wrapper}>
      <div
        ref={contentRef}
        className={`${textClassName} ${s.text} ${expanded ? s.expanded : ""}`}
        style={{ maxHeight }}
      >
        <p ref={textRef}>{text}</p>

        {showButton && isTruncated && (
          <button
            className={`${s.button} ${color ? s[color] : ""}`}
            onClick={toggleExpanded}
          >
            {expanded ? t("showLess") : `... ${t("seeMore")}`}
          </button>
        )}
      </div>
    </div>
  );
};

export default ExpandableText;
