"use client";

import type { ReactElement, ReactNode } from "react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useGalleryStore } from "@/store/use-gallery-store";

export function MoveToAlbumMenu({
  imageId,
  currentAlbumId,
  triggerElement,
  children,
}: {
  imageId: string;
  currentAlbumId: string;
  triggerElement: ReactElement;
  children: ReactNode;
}) {
  const albums = useGalleryStore((s) => s.albums);
  const moveImage = useGalleryStore((s) => s.moveImage);
  const otherAlbums = albums.filter((album) => album.id !== currentAlbumId);

  if (otherAlbums.length === 0) return null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={triggerElement}>{children}</DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {otherAlbums.map((album) => (
          <DropdownMenuItem
            key={album.id}
            onClick={(e) => {
              e.stopPropagation();
              moveImage(imageId, album.id);
            }}
          >
            {album.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
