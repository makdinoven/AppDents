import ReactPixel from "react-facebook-pixel";

const options = {
  autoConfig: true,
  debug: false,
};

const pixelIds = [
  "355039504358349",
  "1105921817166633",
  "975797817469515",
  "650811281430656",
  "24812913481682501",
  "1339550707730116",
"1137652824981294",
"1522877325527377"

];

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

const lowPricePixelId = "1298218948485625";

let lowPricePixelInitialized = false;

export const initLowPricePixel = () => {
  if (!lowPricePixelInitialized) {
    ReactPixel.init(lowPricePixelId, undefined, options);
    lowPricePixelInitialized = true;
  }
};

export const trackLowPricePageView = () => {
  if (lowPricePixelInitialized) {
    ReactPixel.pageView();
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
