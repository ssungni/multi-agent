"use client";

import { useMemo } from "react";
import { ImagesIcon } from "lucide-react";

import { ImageCard } from "@/components/gallery/image-card";
import { useGalleryStore } from "@/store/use-gallery-store";

export function MasonryGrid() {
  const activeAlbumId = useGalleryStore((s) => s.activeAlbumId);
  const allImages = useGalleryStore((s) => s.images);
  const images = useMemo(
    () => allImages.filter((img) => img.albumId === activeAlbumId),
    [allImages, activeAlbumId]
  );

  if (images.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-2 py-24 text-muted-foreground">
        <ImagesIcon className="size-8" />
        <p className="text-sm">아직 생성된 이미지가 없어요. 위에서 프롬프트를 입력해 보세요.</p>
      </div>
    );
  }

  return (
    <div className="columns-2 gap-3 sm:columns-3 xl:columns-4">
      {images.map((image) => (
        <ImageCard key={image.id} image={image} />
      ))}
    </div>
  );
}
