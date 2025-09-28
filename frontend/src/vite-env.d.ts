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
