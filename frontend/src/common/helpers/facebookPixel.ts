import ReactPixel from "react-facebook-pixel";

const options = {
  autoConfig: true,
  debug: false,
};

export const initFacebookPixel = () => {
  ReactPixel.init("355039504358349", undefined, options);
};

export const trackPageView = () => {
  ReactPixel.pageView();
};
