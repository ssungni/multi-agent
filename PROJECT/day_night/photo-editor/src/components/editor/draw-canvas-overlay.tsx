"use client";

import { useEffect, useRef, useState } from "react";

import { useEditorStore } from "@/store/use-editor-store";
import type { StrokePoint } from "@/types";

export function DrawCanvasOverlay() {
  const strokes = useEditorStore((s) => s.strokes);
  const activeTool = useEditorStore((s) => s.activeTool);
  const drawColor = useEditorStore((s) => s.drawColor);
  const drawSize = useEditorStore((s) => s.drawSize);
  const isErasing = useEditorStore((s) => s.isErasing);
  const addStroke = useEditorStore((s) => s.addStroke);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentPoints, setCurrentPoints] = useState<StrokePoint[] | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const { width, height } = container.getBoundingClientRect();
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);

    const allStrokes = currentPoints
      ? [
          ...strokes,
          { id: "_current", points: currentPoints, color: drawColor, size: drawSize, erase: isErasing },
        ]
      : strokes;

    for (const stroke of allStrokes) {
      if (stroke.points.length < 2) continue;
      ctx.globalCompositeOperation = stroke.erase ? "destination-out" : "source-over";
      ctx.strokeStyle = stroke.color;
      ctx.lineWidth = stroke.size;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.beginPath();
      stroke.points.forEach((p, i) => {
        const px = p.x * width;
        const py = p.y * height;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.stroke();
    }
  }, [strokes, currentPoints, drawColor, drawSize, isErasing]);

  function relativePoint(e: React.PointerEvent): StrokePoint {
    const rect = containerRef.current!.getBoundingClientRect();
    return { x: (e.clientX - rect.left) / rect.width, y: (e.clientY - rect.top) / rect.height };
  }

  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (activeTool !== "draw") return;
    e.currentTarget.setPointerCapture(e.pointerId);
    setCurrentPoints([relativePoint(e)]);
  }

  function handlePointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (activeTool !== "draw" || !currentPoints) return;
    setCurrentPoints((pts) => (pts ? [...pts, relativePoint(e)] : pts));
  }

  function handlePointerUp() {
    if (activeTool !== "draw" || !currentPoints) return;
    if (currentPoints.length >= 2) {
      addStroke({
        id: crypto.randomUUID(),
        points: currentPoints,
        color: drawColor,
        size: drawSize,
        erase: isErasing,
      });
    }
    setCurrentPoints(null);
  }

  return (
    <div
      ref={containerRef}
      className="absolute inset-0"
      style={{ pointerEvents: activeTool === "draw" ? "auto" : "none", touchAction: "none" }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      <canvas ref={canvasRef} className="h-full w-full" />
    </div>
  );
}
