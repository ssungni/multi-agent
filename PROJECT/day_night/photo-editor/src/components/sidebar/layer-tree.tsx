"use client";

import { useMemo } from "react";
import { PenLineIcon, TypeIcon, Trash2Icon, WandSparklesIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { buildUnifiedLayers } from "@/lib/unified-layers";
import { useEditorStore } from "@/store/use-editor-store";
import type { DetectedLayer, UnifiedLayer } from "@/types";

function CropThumbnail({ imageUrl, bbox }: { imageUrl: string; bbox: DetectedLayer["bbox"] }) {
  const w = Math.min(0.98, Math.max(0.02, bbox.width));
  const h = Math.min(0.98, Math.max(0.02, bbox.height));
  const posX = (bbox.x / (1 - w)) * 100;
  const posY = (bbox.y / (1 - h)) * 100;

  return (
    <div
      className="size-8 shrink-0 rounded-md bg-neutral-200 bg-cover"
      style={{
        backgroundImage: `url(${imageUrl})`,
        backgroundSize: `${(1 / w) * 100}% ${(1 / h) * 100}%`,
        backgroundPosition: `${posX}% ${posY}%`,
      }}
    />
  );
}

function LayerThumbnail({ layer, imageUrl }: { layer: UnifiedLayer; imageUrl: string }) {
  if (layer.kind === "image" && layer.thumbnailUrl) {
    return (
      <div
        className="size-8 shrink-0 rounded-md bg-neutral-200 bg-cover bg-center"
        style={{ backgroundImage: `url(${layer.thumbnailUrl})` }}
      />
    );
  }
  if (layer.kind === "text") {
    return (
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-neutral-900">
        <TypeIcon className="size-4" style={{ color: layer.color }} />
      </div>
    );
  }
  if (layer.kind === "stroke") {
    return (
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-neutral-100">
        <PenLineIcon className="size-4" style={{ color: layer.color }} />
      </div>
    );
  }
  if (layer.kind === "effect") {
    return (
      <div
        className="size-8 shrink-0 rounded-md bg-neutral-200 bg-cover bg-center"
        style={{ backgroundImage: `url(${imageUrl})`, filter: layer.filter }}
      />
    );
  }
  return <div className="size-8 shrink-0 rounded-md bg-neutral-200" />;
}

function LayerRow({
  id,
  name,
  isSelected,
  onSelect,
  thumbnail,
  extraIcon,
  onDelete,
}: {
  id: string;
  name: string;
  isSelected: boolean;
  onSelect: () => void;
  thumbnail: React.ReactNode;
  extraIcon?: React.ReactNode;
  onDelete?: (e: React.MouseEvent) => void;
}) {
  return (
    <div
      key={id}
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      className={cn(
        "group flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors",
        isSelected ? "bg-accent" : "hover:bg-accent/60"
      )}
    >
      {thumbnail}
      <span className="min-w-0 flex-1 truncate text-sm capitalize">{name}</span>
      {extraIcon}
      {onDelete && (
        <button
          type="button"
          onClick={onDelete}
          aria-label="레이어 삭제"
          className="hidden shrink-0 rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive group-hover:flex"
        >
          <Trash2Icon className="size-3.5" />
        </button>
      )}
    </div>
  );
}

export function LayerTree() {
  const imageUrl = useEditorStore((s) => s.imageUrl);
  const detectedLayers = useEditorStore((s) => s.layers);
  const strokes = useEditorStore((s) => s.strokes);
  const textLayers = useEditorStore((s) => s.textLayers);
  const placedImages = useEditorStore((s) => s.placedImages);
  const activeEffectId = useEditorStore((s) => s.activeEffectId);
  const isSegmenting = useEditorStore((s) => s.isSegmenting);

  const selectedLayerId = useEditorStore((s) => s.selectedLayerId);
  const selectLayer = useEditorStore((s) => s.selectLayer);
  const removeStroke = useEditorStore((s) => s.removeStroke);
  const removeTextLayer = useEditorStore((s) => s.removeTextLayer);
  const removePlacedImage = useEditorStore((s) => s.removePlacedImage);
  const setActiveEffect = useEditorStore((s) => s.setActiveEffect);

  const editedLayers = useMemo(
    () =>
      buildUnifiedLayers({
        detectedLayers: [],
        strokes,
        textLayers,
        placedImages,
        activeEffectId,
      }),
    [strokes, textLayers, placedImages, activeEffectId]
  );

  if (!imageUrl) return null;

  const root = detectedLayers.find((l) => l.id === "layer-root");
  const topLevelObjects = detectedLayers.filter(
    (l) => l.parentId === "layer-root" && !l.isBackground
  );
  const background = detectedLayers.find((l) => l.isBackground);

  function handleEditedDelete(e: React.MouseEvent, layer: UnifiedLayer) {
    e.stopPropagation();
    if (layer.kind === "stroke") removeStroke(layer.id);
    else if (layer.kind === "text") removeTextLayer(layer.id);
    else if (layer.kind === "image") removePlacedImage(layer.id);
    else if (layer.kind === "effect") setActiveEffect(null);
  }

  return (
    <div className="flex flex-col gap-0.5 px-3 py-2">
      {root && (
        <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
          <CropThumbnail imageUrl={imageUrl} bbox={root.bbox} />
          <span className="text-sm font-medium">{root.name}</span>
        </div>
      )}

      <div className="ml-4 flex flex-col gap-0.5 border-l border-border pl-2">
        {isSegmenting && (
          <p className="px-2 py-1.5 text-xs text-muted-foreground">객체를 감지하는 중...</p>
        )}

        {editedLayers.map((layer) => (
          <LayerRow
            key={layer.id}
            id={layer.id}
            name={layer.name}
            isSelected={selectedLayerId === layer.id}
            onSelect={() => selectLayer(layer.id)}
            thumbnail={<LayerThumbnail layer={layer} imageUrl={imageUrl} />}
            extraIcon={
              layer.kind === "effect" ? (
                <WandSparklesIcon className="size-3.5 shrink-0 text-muted-foreground" />
              ) : undefined
            }
            onDelete={(e) => handleEditedDelete(e, layer)}
          />
        ))}

        {topLevelObjects.map((object) => {
          const parts = detectedLayers.filter((l) => l.parentId === object.id);
          return (
            <div key={object.id} className="flex flex-col gap-0.5">
              <LayerRow
                id={object.id}
                name={object.name}
                isSelected={selectedLayerId === object.id}
                onSelect={() => selectLayer(object.id)}
                thumbnail={<CropThumbnail imageUrl={imageUrl} bbox={object.bbox} />}
              />
              {parts.length > 0 && (
                <div className="ml-4 flex flex-col gap-0.5 border-l border-border pl-2">
                  {parts.map((part) => (
                    <LayerRow
                      key={part.id}
                      id={part.id}
                      name={part.name}
                      isSelected={selectedLayerId === part.id}
                      onSelect={() => selectLayer(part.id)}
                      thumbnail={<CropThumbnail imageUrl={imageUrl} bbox={part.bbox} />}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {background && (
          <LayerRow
            id={background.id}
            name="background"
            isSelected={selectedLayerId === background.id}
            onSelect={() => selectLayer(background.id)}
            thumbnail={<CropThumbnail imageUrl={imageUrl} bbox={background.bbox} />}
          />
        )}
      </div>
    </div>
  );
}
