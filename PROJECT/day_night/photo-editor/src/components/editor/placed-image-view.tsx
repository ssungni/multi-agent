"use client";

import Image from "next/image";
import { XIcon } from "lucide-react";

import { useEditorStore } from "@/store/use-editor-store";
import type { PlacedImageLayer } from "@/types";

export function PlacedImageView({ layer }: { layer: PlacedImageLayer }) {
  const removePlacedImage = useEditorStore((s) => s.removePlacedImage);

  return (
    <div
      className="group absolute"
      style={{
        left: `${layer.x * 100}%`,
        top: `${layer.y * 100}%`,
        width: `${layer.width * 100}%`,
        height: `${layer.height * 100}%`,
      }}
    >
      <Image src={layer.url} alt="" fill className="object-contain" draggable={false} />
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          removePlacedImage(layer.id);
        }}
        className="absolute -top-2 -right-2 hidden size-5 items-center justify-center rounded-full bg-neutral-900 text-white group-hover:flex"
      >
        <XIcon className="size-3" />
      </button>
    </div>
  );
}
