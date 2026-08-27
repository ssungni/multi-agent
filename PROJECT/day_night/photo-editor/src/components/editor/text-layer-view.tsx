"use client";

import { XIcon } from "lucide-react";

import { useEditorStore } from "@/store/use-editor-store";
import type { TextLayer } from "@/types";

export function TextLayerView({ layer }: { layer: TextLayer }) {
  const updateTextLayer = useEditorStore((s) => s.updateTextLayer);
  const removeTextLayer = useEditorStore((s) => s.removeTextLayer);
  const activeTool = useEditorStore((s) => s.activeTool);

  const interactive = activeTool === "select" || activeTool === "text";

  return (
    <div
      className="group absolute -translate-x-1/2 -translate-y-1/2"
      style={{ left: `${layer.x * 100}%`, top: `${layer.y * 100}%` }}
    >
      <div
        contentEditable={interactive}
        suppressContentEditableWarning
        onClick={(e) => e.stopPropagation()}
        onBlur={(e) => updateTextLayer(layer.id, { text: e.currentTarget.textContent ?? "" })}
        className="min-w-[2ch] px-1 font-semibold outline-none"
        style={{
          color: layer.color,
          fontSize: layer.fontSize,
          cursor: interactive ? "text" : "default",
          pointerEvents: interactive ? "auto" : "none",
        }}
      >
        {layer.text}
      </div>
      {interactive && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            removeTextLayer(layer.id);
          }}
          className="absolute -top-2 -right-2 hidden size-4 items-center justify-center rounded-full bg-neutral-900 text-white group-hover:flex"
        >
          <XIcon className="size-3" />
        </button>
      )}
    </div>
  );
}
