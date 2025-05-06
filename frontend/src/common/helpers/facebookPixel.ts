import ReactPixel from "react-facebook-pixel";

const options = {
  autoConfig: true,
  debug: false,
};

const pixelIds = ["355039504358349", "1105921817166633"];

let initialized = false;

export const initFacebookPixel = () => {
  if (!initialized) {
    pixelIds.forEach((id) => {
      ReactPixel.init(id, undefined, options);
    });
    initialized = true;
  }
};

export const trackPageView = () => {
  ReactPixel.pageView();
};
