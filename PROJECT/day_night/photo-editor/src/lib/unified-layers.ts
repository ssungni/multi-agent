import { getEffectById } from "@/lib/effect-presets";
import type { DetectedLayer, DrawStroke, PlacedImageLayer, Rect, TextLayer, UnifiedLayer } from "@/types";

export function strokeBBox(stroke: DrawStroke): Rect {
  const xs = stroke.points.map((p) => p.x);
  const ys = stroke.points.map((p) => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const pad = 0.015;
  const x = Math.max(0, minX - pad);
  const y = Math.max(0, minY - pad);
  return {
    x,
    y,
    width: Math.min(1 - x, maxX - minX + pad * 2),
    height: Math.min(1 - y, maxY - minY + pad * 2),
  };
}

export function buildUnifiedLayers(params: {
  detectedLayers: DetectedLayer[];
  strokes: DrawStroke[];
  textLayers: TextLayer[];
  placedImages: PlacedImageLayer[];
  activeEffectId: string | null;
}): UnifiedLayer[] {
  const { detectedLayers, strokes, textLayers, placedImages, activeEffectId } = params;
  const result: UnifiedLayer[] = [];

  const effect = getEffectById(activeEffectId);
  if (effect) {
    result.push({ id: "unified-effect", kind: "effect", name: effect.name, bbox: null, filter: effect.filter });
  }

  [...placedImages]
    .map((layer, i) => ({ layer, name: `Image ${i + 1}` }))
    .reverse()
    .forEach(({ layer, name }) => {
      result.push({
        id: layer.id,
        kind: "image",
        name,
        bbox: { x: layer.x, y: layer.y, width: layer.width, height: layer.height },
        thumbnailUrl: layer.url,
      });
    });

  [...textLayers].reverse().forEach((layer) => {
    result.push({
      id: layer.id,
      kind: "text",
      name: layer.text.trim() || "Text",
      bbox: { x: layer.x - 0.05, y: layer.y - 0.03, width: 0.1, height: 0.06 },
      color: layer.color,
    });
  });

  [...strokes]
    .map((stroke, i) => ({ stroke, name: `${stroke.erase ? "Eraser" : "Drawing"} ${i + 1}` }))
    .reverse()
    .forEach(({ stroke, name }) => {
      result.push({
        id: stroke.id,
        kind: "stroke",
        name,
        bbox: strokeBBox(stroke),
        color: stroke.color,
      });
    });

  detectedLayers
    .filter((l) => l.id !== "layer-root" && !l.isBackground)
    .forEach((layer) => {
      result.push({ id: layer.id, kind: "detected", name: layer.name, bbox: layer.bbox });
    });

  const background = detectedLayers.find((l) => l.isBackground);
  if (background) {
    result.push({ id: background.id, kind: "background", name: "background", bbox: background.bbox });
  }

  return result;
}
