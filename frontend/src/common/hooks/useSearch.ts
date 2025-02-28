import { useState } from "react";

type SearchKey<T> = keyof T;

export function useSearch<T>(items: T[], keys: SearchKey<T>[]) {
  const [searchQuery, setSearchQuery] = useState("");

  const normalize = (str: string) =>
    str.toLowerCase().replace(/\s+/g, " ").trim();

  const filteredItems = items.filter((item) =>
    keys.some((key) =>
      normalize(String(item[key])).includes(normalize(searchQuery)),
    ),
  );

  return { searchQuery, setSearchQuery, filteredItems };
}
