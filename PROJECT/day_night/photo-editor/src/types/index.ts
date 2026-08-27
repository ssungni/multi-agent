export type ToolId =
  | "select"
  | "spotlight"
  | "draw"
  | "add-object"
  | "text"
  | "add-image"
  | "add-effects";

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectedLayer {
  id: string;
  name: string;
  bbox: Rect;
  parentId?: string;
  isBackground?: boolean;
}

export interface TextLayer {
  id: string;
  x: number;
  y: number;
  text: string;
  color: string;
  fontSize: number;
}

export interface StrokePoint {
  x: number;
  y: number;
}

export interface DrawStroke {
  id: string;
  points: StrokePoint[];
  color: string;
  size: number;
  erase?: boolean;
}

export interface PlacedImageLayer {
  id: string;
  url: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: number;
}

export type EffectCategory = "textures" | "light" | "color";

export interface EffectPreset {
  id: string;
  name: string;
  category: EffectCategory;
  filter: string;
}

export interface Album {
  id: string;
  name: string;
  createdAt: number;
  updatedAt: number;
}

export interface SerializedSession {
  imageUrl: string | null;
  history: string[];
  future: string[];
  layers: DetectedLayer[];
  textLayers: TextLayer[];
  placedImages: PlacedImageLayer[];
  strokes: DrawStroke[];
  activeEffectId: string | null;
  chatMessages: ChatMessage[];
}

export type AppView = "start" | "workspace" | "editor";

export type UnifiedLayerKind =
  | "root"
  | "detected"
  | "background"
  | "stroke"
  | "text"
  | "image"
  | "effect";

export interface UnifiedLayer {
  id: string;
  kind: UnifiedLayerKind;
  name: string;
  bbox: Rect | null;
  color?: string;
  thumbnailUrl?: string;
  filter?: string;
}
