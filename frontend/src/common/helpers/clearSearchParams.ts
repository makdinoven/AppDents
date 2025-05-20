import { URLSearchParamsInit } from "react-router-dom";

export const clearSearchParams = (
  setSearchParams: (
    nextInit: URLSearchParamsInit,
    options?: { replace?: boolean },
  ) => void,
  searchParams: URLSearchParams,
  keysToKeep: string[] = [],
) => {
  if (keysToKeep.length === 0) {
    setSearchParams({});
    return;
  }

  const newParams = new URLSearchParams();

  keysToKeep.forEach((key) => {
    const value = searchParams.get(key);
    if (value !== null) {
      newParams.set(key, value);
    }
  });

  setSearchParams(newParams);
};
