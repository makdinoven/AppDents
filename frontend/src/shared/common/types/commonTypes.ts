import { ReactNode } from "react";

export type Brand = "dents" | "medg";
export type SidebarShellData =
  | {
      type: "link";
      path: string;
      title: string;
      icon?: ReactNode;
    }
  | {
      type: "action";
      title: string;
      icon?: ReactNode;
      onClick: () => void;
    }
  | {
      type: "custom";
      title?: string;
      icon?: ReactNode;
      render: () => ReactNode;
    };
