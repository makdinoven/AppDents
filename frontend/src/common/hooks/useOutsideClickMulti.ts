import { useEffect } from "react";

const useOutsideClickMulti = (
  refs: React.RefObject<HTMLElement | null>[],
  callback: () => void,
) => {
  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const isInside = refs.some(
        (ref) => ref.current && ref.current.contains(event.target as Node),
      );

      if (!isInside) {
        callback();
      }
    };

    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("mousedown", handleClick);
    };
  }, [refs, callback]);
};

export default useOutsideClickMulti;
