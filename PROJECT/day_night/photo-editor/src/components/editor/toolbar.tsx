"use client";

import { useRef } from "react";
import {
  BoxIcon,
  EraserIcon,
  ImagePlusIcon,
  MousePointer2Icon,
  PenLineIcon,
  SquareDashedIcon,
  TypeIcon,
  WandSparklesIcon,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useEditorStore } from "@/store/use-editor-store";
import type { ToolId } from "@/types";

const TOOLS: { id: ToolId; icon: LucideIcon; label: string }[] = [
  { id: "select", icon: MousePointer2Icon, label: "Select objects" },
  { id: "spotlight", icon: SquareDashedIcon, label: "Spotlight" },
  { id: "draw", icon: PenLineIcon, label: "Draw" },
  { id: "add-object", icon: BoxIcon, label: "Add objects" },
  { id: "text", icon: TypeIcon, label: "Text" },
  { id: "add-image", icon: ImagePlusIcon, label: "Add image" },
  { id: "add-effects", icon: WandSparklesIcon, label: "Add effects" },
];

const DRAW_COLORS = [
  "#ef4444",
  "#f97316",
  "#eab308",
  "#22c55e",
  "#3b82f6",
  "#8b5cf6",
  "#111827",
  "#ffffff",
];

export function Toolbar() {
  const activeTool = useEditorStore((s) => s.activeTool);
  const setActiveTool = useEditorStore((s) => s.setActiveTool);
  const drawColor = useEditorStore((s) => s.drawColor);
  const setDrawColor = useEditorStore((s) => s.setDrawColor);
  const drawSize = useEditorStore((s) => s.drawSize);
  const setDrawSize = useEditorStore((s) => s.setDrawSize);
  const isErasing = useEditorStore((s) => s.isErasing);
  const setIsErasing = useEditorStore((s) => s.setIsErasing);
  const addPlacedImage = useEditorStore((s) => s.addPlacedImage);
  const openEffectsPanel = useEditorStore((s) => s.openEffectsPanel);

  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleToolClick(id: ToolId) {
    if (id === "add-image") {
      fileInputRef.current?.click();
      return;
    }
    setActiveTool(id);
    if (id === "add-effects") openEffectsPanel();
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      addPlacedImage(reader.result as string, 0.3, 0.3, 0.4, 0.4);
    };
    reader.readAsDataURL(file);
    setActiveTool("select");
  }

  return (
    <div className="absolute bottom-6 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2">
      {activeTool === "draw" && (
        <div className="flex items-center gap-3 rounded-full border border-border bg-popover px-4 py-2 shadow-lg">
          <Button
            size="icon-sm"
            variant={isErasing ? "ghost" : "secondary"}
            aria-label="펜"
            onClick={() => setIsErasing(false)}
          >
            <PenLineIcon />
          </Button>
          <Button
            size="icon-sm"
            variant={isErasing ? "secondary" : "ghost"}
            aria-label="지우개"
            onClick={() => setIsErasing(true)}
          >
            <EraserIcon />
          </Button>
          <div className="flex items-center gap-2">
            <span
              className="shrink-0 rounded-full bg-neutral-900"
              style={{
                width: Math.min(drawSize, 24),
                height: Math.min(drawSize, 24),
              }}
              aria-hidden
            />
            <Slider
              value={[drawSize]}
              min={2}
              max={40}
              step={1}
              onValueChange={(v) => setDrawSize(Array.isArray(v) ? v[0] : v)}
              className="w-24"
            />
            <span className="w-7 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
              {drawSize}
            </span>
          </div>
          <div className="flex items-center gap-1">
            {DRAW_COLORS.map((color) => (
              <button
                key={color}
                type="button"
                aria-label={color}
                onClick={() => setDrawColor(color)}
                className={cn(
                  "size-5 rounded-full border-2",
                  drawColor === color ? "border-blue-500" : "border-transparent"
                )}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-1 rounded-full border border-border bg-popover p-1.5 shadow-lg">
        {TOOLS.map(({ id, icon: Icon, label }) => (
          <Button
            key={id}
            size="icon-sm"
            variant={activeTool === id ? "default" : "ghost"}
            aria-label={label}
            onClick={() => handleToolClick(id)}
          >
            <Icon />
          </Button>
        ))}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}
