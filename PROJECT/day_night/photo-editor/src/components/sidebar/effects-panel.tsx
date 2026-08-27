"use client";

import { XIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EFFECT_PRESETS } from "@/lib/effect-presets";
import { useEditorStore } from "@/store/use-editor-store";
import type { EffectCategory, EffectPreset } from "@/types";

function PresetGrid({
  presets,
  imageUrl,
  activeEffectId,
  onSelect,
}: {
  presets: EffectPreset[];
  imageUrl: string;
  activeEffectId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {presets.map((preset) => (
        <button
          key={preset.id}
          type="button"
          onClick={() => onSelect(preset.id)}
          className="flex flex-col items-center gap-1"
        >
          <div
            className={cn(
              "aspect-square w-full overflow-hidden rounded-lg ring-2 ring-offset-1",
              activeEffectId === preset.id ? "ring-blue-500" : "ring-transparent"
            )}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={imageUrl}
              alt={preset.name}
              className="h-full w-full object-cover"
              style={{ filter: preset.filter }}
            />
          </div>
          <span className="w-full truncate text-center text-xs text-muted-foreground">
            {preset.name}
          </span>
        </button>
      ))}
    </div>
  );
}

function CategorySection({
  title,
  category,
  imageUrl,
  activeEffectId,
  onSelect,
}: {
  title: string;
  category: EffectCategory;
  imageUrl: string;
  activeEffectId: string | null;
  onSelect: (id: string) => void;
}) {
  const presets = EFFECT_PRESETS.filter((p) => p.category === category);
  return (
    <div>
      <p className="mb-2 text-xs font-medium text-muted-foreground">{title}</p>
      <PresetGrid presets={presets} imageUrl={imageUrl} activeEffectId={activeEffectId} onSelect={onSelect} />
    </div>
  );
}

export function EffectsPanel() {
  const imageUrl = useEditorStore((s) => s.imageUrl);
  const activeEffectId = useEditorStore((s) => s.activeEffectId);
  const setActiveEffect = useEditorStore((s) => s.setActiveEffect);
  const confirmEffects = useEditorStore((s) => s.confirmEffects);
  const cancelEffects = useEditorStore((s) => s.cancelEffects);
  const setActiveTool = useEditorStore((s) => s.setActiveTool);

  if (!imageUrl) return null;

  function handleCancel() {
    cancelEffects();
    setActiveTool("select");
  }

  function handleDone() {
    confirmEffects();
    setActiveTool("select");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="font-semibold">Add effect</h2>
        <Button size="icon-sm" variant="ghost" aria-label="닫기" onClick={handleCancel}>
          <XIcon />
        </Button>
      </div>

      <Tabs defaultValue="all" className="flex-1 overflow-hidden">
        <TabsList className="mx-4 mt-3 w-fit">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="saved">Saved</TabsTrigger>
          <TabsTrigger value="textures">Textures</TabsTrigger>
          <TabsTrigger value="light">Light</TabsTrigger>
          <TabsTrigger value="color">Color</TabsTrigger>
        </TabsList>

        <div className="h-[calc(100%-3rem)] overflow-y-auto px-4 py-3">
          <TabsContent value="all" className="flex flex-col gap-5">
            <CategorySection
              title="Textures"
              category="textures"
              imageUrl={imageUrl}
              activeEffectId={activeEffectId}
              onSelect={setActiveEffect}
            />
            <CategorySection
              title="Light"
              category="light"
              imageUrl={imageUrl}
              activeEffectId={activeEffectId}
              onSelect={setActiveEffect}
            />
            <CategorySection
              title="Color"
              category="color"
              imageUrl={imageUrl}
              activeEffectId={activeEffectId}
              onSelect={setActiveEffect}
            />
          </TabsContent>

          <TabsContent value="saved">
            <p className="py-8 text-center text-sm text-muted-foreground">저장된 효과가 없습니다.</p>
          </TabsContent>

          <TabsContent value="textures">
            <PresetGrid
              presets={EFFECT_PRESETS.filter((p) => p.category === "textures")}
              imageUrl={imageUrl}
              activeEffectId={activeEffectId}
              onSelect={setActiveEffect}
            />
          </TabsContent>

          <TabsContent value="light">
            <PresetGrid
              presets={EFFECT_PRESETS.filter((p) => p.category === "light")}
              imageUrl={imageUrl}
              activeEffectId={activeEffectId}
              onSelect={setActiveEffect}
            />
          </TabsContent>

          <TabsContent value="color">
            <PresetGrid
              presets={EFFECT_PRESETS.filter((p) => p.category === "color")}
              imageUrl={imageUrl}
              activeEffectId={activeEffectId}
              onSelect={setActiveEffect}
            />
          </TabsContent>
        </div>
      </Tabs>

      <div className="flex justify-end gap-2 border-t border-border p-3">
        <Button variant="outline" onClick={handleCancel}>
          Cancel
        </Button>
        <Button onClick={handleDone}>Done</Button>
      </div>
    </div>
  );
}
