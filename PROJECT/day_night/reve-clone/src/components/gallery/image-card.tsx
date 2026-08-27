"use client";

import Image from "next/image";
import { DownloadIcon, FolderInputIcon, Trash2Icon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { MoveToAlbumMenu } from "@/components/gallery/move-to-album-menu";
import { useGalleryStore } from "@/store/use-gallery-store";
import type { GeneratedImage } from "@/types";

export function ImageCard({ image }: { image: GeneratedImage }) {
  const selectImage = useGalleryStore((s) => s.selectImage);
  const deleteImage = useGalleryStore((s) => s.deleteImage);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => selectImage(image.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectImage(image.id);
        }
      }}
      className="group relative mb-3 block w-full cursor-pointer break-inside-avoid overflow-hidden rounded-xl bg-muted text-left"
    >
      <Image
        src={image.url}
        alt={image.prompt}
        width={image.width}
        height={image.height}
        className="w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
      />

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />

      <p className="pointer-events-none absolute inset-x-0 bottom-0 line-clamp-2 p-3 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100">
        {image.prompt}
      </p>

      <div className="absolute top-2 right-2 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          size="icon-sm"
          variant="secondary"
          aria-label="다운로드"
          nativeButton={false}
          render={
            <a
              href={image.url}
              download={`${image.id}.jpg`}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
            />
          }
        >
          <DownloadIcon />
        </Button>
        <MoveToAlbumMenu
          imageId={image.id}
          currentAlbumId={image.albumId}
          triggerElement={
            <Button
              size="icon-sm"
              variant="secondary"
              aria-label="다른 앨범으로 이동"
              onClick={(e) => e.stopPropagation()}
            />
          }
        >
          <FolderInputIcon />
        </MoveToAlbumMenu>
        <Button
          size="icon-sm"
          variant="secondary"
          aria-label="삭제"
          onClick={(e) => {
            e.stopPropagation();
            deleteImage(image.id);
          }}
        >
          <Trash2Icon />
        </Button>
      </div>
    </div>
  );
}
