export const DEFAULT_SCALE = 0.75;

export const screenResolutionMap = new Map([
  ["desktop", { width: 1440, pageWidth: 600 }],
  ["middle", { width: 1024, pageWidth: 500 }],
  ["tablet", { width: 768, pageWidth: 450 }],
  ["mobile", { width: 576, pageWidth: 300 }],
]);

export const scales = [
  { value: 0.5, label: "50%" },
  { value: 0.75, label: "75%" },
  { value: 1, label: "100%" },
  { value: 1.25, label: "125%" },
  { value: 1.5, label: "150%" },
  { value: 2, label: "200%" },
];

export const PDF_READER_FULLSCREEN_KEY = "pdf-reader-fullscreen";
export const PDF_READER_SCALE_KEY = "pdf-reader-scale";
