import ReactPixel from "react-facebook-pixel";

const options = {
  autoConfig: true,
  debug: false,
};

const pixelIds = ["355039504358349", "1105921817166633", "975797817469515"];

const languagePixelIds: Record<string, string> = {
  IT: "722350576947991",
  RU: "1250960943261191",
  ES: "2237430456676528",
  EN: "2553300781678148",
};

let initialized = false;
const initializedLanguagePixel: { pixelId?: string } = {};

export const initFacebookPixel = () => {
  if (!initialized) {
    pixelIds.forEach((id) => {
      ReactPixel.init(id, undefined, options);
    });
    initialized = true;
  }
};

export const initLanguagePixel = (lang: string) => {
  const pixelId = languagePixelIds[lang];
  if (!pixelId) return;

  if (initializedLanguagePixel.pixelId !== pixelId) {
    ReactPixel.init(pixelId, undefined, options);
    initializedLanguagePixel.pixelId = pixelId;
  }
};

export const trackPageView = () => {
  ReactPixel.pageView();
};
