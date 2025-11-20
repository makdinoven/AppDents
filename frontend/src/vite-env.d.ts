/// <reference types="vite/client" />
declare module "*.svg?react" {
  import * as React from "react";
  const ReactComponent: React.FC<React.SVGProps<SVGSVGElement>>;
  export default ReactComponent;
}

declare module "*.json" {
  const value: any;
  export default value;
}

declare module "@hero-bg" {
  const src: string;
  export default src;
}

declare module "@hero-bg-mobile" {
  const src: string;
  export default src;
}

declare module "@logo" {
  import { FC, SVGProps } from "react";
  const AppLogo: FC<SVGProps<SVGSVGElement>>;
  export default AppLogo;
}
