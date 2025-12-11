import { useEffect, useRef } from "react";
import { ListQueryParams } from "../../components/list/model/useListQueryParams.ts";

type SetFn = (next: Partial<ListQueryParams>) => void;

export function useResetPageOnChange<T>(value: T, set: SetFn) {
  const firstRenderRef = useRef(true);
  const prevValueRef = useRef<T>(value);

  useEffect(() => {
    if (firstRenderRef.current) {
      firstRenderRef.current = false;
      prevValueRef.current = value;
      return;
    }

    if (prevValueRef.current !== value) {
      set({ page: 1 });
      prevValueRef.current = value;
    }
  }, [value, set]);
}
