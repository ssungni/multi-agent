"use client";

import { useRef, useState } from "react";
import { Loader2Icon } from "lucide-react";

import { useEditorStore } from "@/store/use-editor-store";
import { getEffectById } from "@/lib/effect-presets";
import { buildUnifiedLayers } from "@/lib/unified-layers";
import { BoundingBox } from "@/components/editor/bounding-box";
import { DrawCanvasOverlay } from "@/components/editor/draw-canvas-overlay";
import { SpotlightOverlay } from "@/components/editor/spotlight-overlay";
import { TextLayerView } from "@/components/editor/text-layer-view";
import { PlacedImageView } from "@/components/editor/placed-image-view";
import { AddObjectPopover } from "@/components/editor/add-object-popover";
import type { Rect } from "@/types";

function containsPoint(bbox: Rect, x: number, y: number) {
  return x >= bbox.x && x <= bbox.x + bbox.width && y >= bbox.y && y <= bbox.y + bbox.height;
}

export function CanvasStage() {
  const imageUrl = useEditorStore((s) => s.imageUrl);
  const layers = useEditorStore((s) => s.layers);
  const selectedLayerId = useEditorStore((s) => s.selectedLayerId);
  const selectLayer = useEditorStore((s) => s.selectLayer);
  const activeTool = useEditorStore((s) => s.activeTool);
  const activeEffectId = useEditorStore((s) => s.activeEffectId);
  const isSegmenting = useEditorStore((s) => s.isSegmenting);
  const isBusy = useEditorStore((s) => s.isBusy);
  const strokes = useEditorStore((s) => s.strokes);
  const textLayers = useEditorStore((s) => s.textLayers);
  const placedImages = useEditorStore((s) => s.placedImages);
  const addTextLayer = useEditorStore((s) => s.addTextLayer);
  const addObjectAt = useEditorStore((s) => s.addObjectAt);

  const containerRef = useRef<HTMLDivElement>(null);
  const [pendingObjectPos, setPendingObjectPos] = useState<{ x: number; y: number } | null>(null);

  if (!imageUrl) return null;

  const objectLayers = layers.filter((l) => l.id !== "layer-root" && !l.isBackground);
  const filter = getEffectById(activeEffectId)?.filter;

  const unifiedLayers = buildUnifiedLayers({
    detectedLayers: layers,
    strokes,
    textLayers,
    placedImages,
    activeEffectId,
  });
  const selectedUnifiedLayer = unifiedLayers.find((l) => l.id === selectedLayerId);

  function relativePoint(e: React.MouseEvent) {
    const rect = containerRef.current!.getBoundingClientRect();
    return { x: (e.clientX - rect.left) / rect.width, y: (e.clientY - rect.top) / rect.height };
  }

  function handleBaseClick(e: React.MouseEvent) {
    const point = relativePoint(e);

    if (activeTool === "select") {
      const matches = objectLayers.filter((l) => containsPoint(l.bbox, point.x, point.y));
      matches.sort((a, b) => a.bbox.width * a.bbox.height - b.bbox.width * b.bbox.height);
      selectLayer(matches[0]?.id ?? null);
    } else if (activeTool === "text") {
      addTextLayer(point.x, point.y);
    } else if (activeTool === "add-object") {
      setPendingObjectPos(point);
    }
  }

  return (
    <div className="relative flex flex-1 items-center justify-center overflow-hidden p-8">
      <div ref={containerRef} className="relative inline-block" onClick={handleBaseClick}>
        {/* Natural intrinsic sizing is required so this container's rendered
            box exactly matches the image (no letterboxing), since every
            overlay below is positioned with percentages relative to it.
            next/image needs predeclared width/height or a fill parent,
            neither of which works for arbitrary user uploads. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt="editing target"
          className="block max-h-[70vh] w-auto max-w-full cursor-crosshair rounded-lg select-none"
          style={{ filter }}
          draggable={false}
        />

        {selectedUnifiedLayer && selectedUnifiedLayer.bbox && (
          <BoundingBox name={selectedUnifiedLayer.name} bbox={selectedUnifiedLayer.bbox} />
        )}

        <DrawCanvasOverlay />
        <SpotlightOverlay />

        {textLayers.map((layer) => (
          <TextLayerView key={layer.id} layer={layer} />
        ))}
        {placedImages.map((layer) => (
          <PlacedImageView key={layer.id} layer={layer} />
        ))}

        {pendingObjectPos && (
          <AddObjectPopover
            x={pendingObjectPos.x}
            y={pendingObjectPos.y}
            onCancel={() => setPendingObjectPos(null)}
            onSubmit={(prompt) => {
              void addObjectAt(prompt, pendingObjectPos.x, pendingObjectPos.y);
              setPendingObjectPos(null);
            }}
          />
        )}

        {(isSegmenting || isBusy) && (
          <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-black/30">
            <Loader2Icon className="size-8 animate-spin text-white" />
          </div>
        )}
      </div>
    </div>
  );
}
