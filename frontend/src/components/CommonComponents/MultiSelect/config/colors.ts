import { Brand } from "../../../../common/types/commonTypes.ts";

export const HOVER_COLOR = "rgba(100, 116, 139, 0.1)";
const COLORS: Record<Brand, { PRIMARY: string; ACCENT: string }> = {
  dents: {
    PRIMARY: "#7FDFD5",
    ACCENT: "#01433D",
  },

  medg: {
    PRIMARY: "#79CEE7",
    ACCENT: "#00304D",
  },
};

const brand = (import.meta.env.VITE_BRAND as Brand) || "dents";
export const { PRIMARY: PRIMARY_COLOR, ACCENT: ACCENT_COLOR } = COLORS[brand];
export const BACKGROUND_COLOR = "#EDF8FF";
