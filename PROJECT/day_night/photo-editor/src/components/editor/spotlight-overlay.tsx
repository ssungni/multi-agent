"use client";

import { useState } from "react";

import { useEditorStore } from "@/store/use-editor-store";

export function SpotlightOverlay() {
  const activeTool = useEditorStore((s) => s.activeTool);
  const spotlightRect = useEditorStore((s) => s.spotlightRect);
  const setSpotlightRect = useEditorStore((s) => s.setSpotlightRect);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);

  function relativePoint(e: React.PointerEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: (e.clientX - rect.left) / rect.width, y: (e.clientY - rect.top) / rect.height };
  }

  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (activeTool !== "spotlight") return;
    e.currentTarget.setPointerCapture(e.pointerId);
    const p = relativePoint(e);
    setStart(p);
    setSpotlightRect({ x: p.x, y: p.y, width: 0, height: 0 });
  }

  function handlePointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (activeTool !== "spotlight" || !start) return;
    const p = relativePoint(e);
    setSpotlightRect({
      x: Math.min(start.x, p.x),
      y: Math.min(start.y, p.y),
      width: Math.abs(p.x - start.x),
      height: Math.abs(p.y - start.y),
    });
  }

  function handlePointerUp() {
    setStart(null);
  }

  return (
    <div
      className="absolute inset-0"
      style={{ pointerEvents: activeTool === "spotlight" ? "auto" : "none", touchAction: "none" }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      {spotlightRect && (
        <div
          className="pointer-events-none absolute border-2 border-dashed border-white bg-white/10"
          style={{
            left: `${spotlightRect.x * 100}%`,
            top: `${spotlightRect.y * 100}%`,
            width: `${spotlightRect.width * 100}%`,
            height: `${spotlightRect.height * 100}%`,
          }}
        />
      )}
    </div>
  );
}
