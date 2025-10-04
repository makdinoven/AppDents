import { useRef, useEffect, useCallback } from "react";

export function useThrottle<T extends (...args: any[]) => void>(
  callback: T,
  delay: number,
): T {
  const lastCall = useRef<number>(0);
  const savedCallback = useRef<T>(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  return useCallback(
    ((...args: any[]) => {
      const now = Date.now();
      if (now - lastCall.current >= delay) {
        lastCall.current = now;
        savedCallback.current(...args);
      }
    }) as T,
    [delay],
  );
}
