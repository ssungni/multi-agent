export type AspectRatio = "1:1" | "3:4" | "4:3" | "9:16" | "16:9";

export const ASPECT_RATIOS: { value: AspectRatio; label: string; w: number; h: number }[] = [
  { value: "1:1", label: "1:1 정사각형", w: 512, h: 512 },
  { value: "3:4", label: "3:4 세로", w: 512, h: 683 },
  { value: "4:3", label: "4:3 가로", w: 683, h: 512 },
  { value: "9:16", label: "9:16 세로", w: 512, h: 910 },
  { value: "16:9", label: "16:9 가로", w: 910, h: 512 },
];

export const IMAGE_COUNTS = [1, 2, 4] as const;
export type ImageCount = (typeof IMAGE_COUNTS)[number];

export interface GeneratedImage {
  id: string;
  albumId: string;
  url: string;
  prompt: string;
  ratio: AspectRatio;
  width: number;
  height: number;
  createdAt: number;
}

export interface Album {
  id: string;
  name: string;
}
